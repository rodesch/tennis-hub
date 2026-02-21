"""
SQLite cache manager for Tennis Hub.
Adapted from gdelt-insights-dashboard/cache_manager.py
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Any, Optional
from pathlib import Path

from app.config import DB_PATH


class CacheManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    created_at TEXT,
                    expires_at TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expires ON cache_entries(expires_at)")
            conn.commit()

    @staticmethod
    def make_key(prefix: str, **kwargs) -> str:
        params = json.dumps(sorted(kwargs.items()), sort_keys=True)
        h = hashlib.md5(params.encode()).hexdigest()
        return f"{prefix}:{h}"

    def get(self, key: str) -> Optional[Any]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT value FROM cache_entries WHERE key=? AND expires_at > ?",
                (key, datetime.utcnow().isoformat())
            ).fetchone()
        if row:
            return json.loads(row[0])
        return None

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        from datetime import timedelta
        now = datetime.utcnow()
        expires = (now + timedelta(seconds=ttl_seconds)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache_entries (key, value, created_at, expires_at) VALUES (?,?,?,?)",
                (key, json.dumps(value), now.isoformat(), expires)
            )
            conn.commit()

    def cleanup(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM cache_entries WHERE expires_at <= ?",
                (datetime.utcnow().isoformat(),)
            )
            conn.commit()
            return cursor.rowcount

    def stats(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM cache_entries").fetchone()[0]
            expired = conn.execute(
                "SELECT COUNT(*) FROM cache_entries WHERE expires_at <= ?",
                (datetime.utcnow().isoformat(),)
            ).fetchone()[0]
        return {"total": total, "expired": expired, "valid": total - expired}


cache = CacheManager()
