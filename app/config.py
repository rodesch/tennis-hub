"""
Tennis Hub - Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = "tennisapi1.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}/api/tennis"

# Cache TTLs in seconds
CACHE_TTL = {
    "rankings": 24 * 3600,     # 24h
    "results": 4 * 3600,       # 4h
    "calendar": 24 * 3600,     # 24h
    "h2h": 12 * 3600,          # 12h
    "draws": 6 * 3600,         # 6h
    "player": 12 * 3600,       # 12h
    "search": 1 * 3600,        # 1h
}

PORT = int(os.getenv("PORT", "5004"))
# Use /tmp on Vercel (read-only fs), local data/ otherwise
_default_db = Path("/tmp/tennis-cache.db") if os.getenv("VERCEL") else Path(__file__).parent.parent / "data" / "cache.db"
DB_PATH = Path(os.getenv("DB_PATH", str(_default_db)))
