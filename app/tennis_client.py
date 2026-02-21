"""
TennisApi (tennis-api-atp-wta-itf) client with aggressive caching.
Base URL: https://tennis-api-atp-wta-itf.p.rapidapi.com/tennis/v2/
Every method checks cache first; only calls API on cache miss.
"""

import httpx
import logging
from datetime import date as dt, datetime
from typing import Optional

from app.config import RAPIDAPI_KEY, RAPIDAPI_HOST, BASE_URL, CACHE_TTL
from app.cache import cache

logger = logging.getLogger(__name__)

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": RAPIDAPI_HOST,
}


class TennisClient:
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(headers=HEADERS, timeout=15.0)
        return self._client

    async def _fetch(self, path: str, params: dict = None) -> dict:
        """Make a real API call, log it for quota tracking."""
        url = f"{BASE_URL}/{path}"
        client = await self._get_client()
        logger.warning("API CALL: %s params=%s", url, params)
        resp = await client.get(url, params=params or {})
        resp.raise_for_status()
        return resp.json()

    async def _cached(self, cache_key: str, ttl: int, path: str, params: dict = None) -> dict:
        hit = cache.get(cache_key)
        if hit is not None:
            logger.debug("Cache HIT: %s", cache_key)
            return hit
        data = await self._fetch(path, params)
        cache.set(cache_key, data, ttl)
        return data

    # ---- Public methods ----

    async def get_rankings(self, type: str = "atp") -> dict:
        """Singles rankings. type: 'atp' | 'wta' | 'itf'"""
        t = type.lower()
        key = cache.make_key("rankings", type=t)
        return await self._cached(key, CACHE_TTL["rankings"], f"{t}/ranking/singles/")

    async def get_results(self, date: str = None, type: str = "atp") -> dict:
        """Match fixtures/results for a date (YYYY-MM-DD). Defaults to today."""
        d = date or dt.today().isoformat()
        t = type.lower()
        key = cache.make_key("results", date=d, type=t)
        return await self._cached(key, CACHE_TTL["results"], f"{t}/fixtures/{d}")

    async def get_calendar(self, type: str = "atp") -> dict:
        """Tournament calendar for the current year."""
        t = type.lower()
        year = datetime.now().year
        key = cache.make_key("calendar", type=t, year=year)
        return await self._cached(key, CACHE_TTL["calendar"], f"{t}/tournament/calendar/{year}")

    async def get_h2h(self, player1_id: int, player2_id: int, type: str = "atp") -> dict:
        """Head-to-head info between two players."""
        t = type.lower()
        key = cache.make_key("h2h", p1=player1_id, p2=player2_id, type=t)
        return await self._cached(
            key, CACHE_TTL["h2h"], f"{t}/h2h/info/{player1_id}/{player2_id}/"
        )

    async def get_draws(self, tournament_id: int, type: str = "atp") -> dict:
        """Tournament results/draw for a given tournament ID."""
        t = type.lower()
        key = cache.make_key("draws", tid=tournament_id, type=t)
        return await self._cached(key, CACHE_TTL["draws"], f"{t}/tournament/results/{tournament_id}")

    async def get_player(self, player_id: int, type: str = "atp") -> dict:
        """Player profile."""
        t = type.lower()
        key = cache.make_key("player", pid=player_id, type=t)
        return await self._cached(key, CACHE_TTL["player"], f"{t}/player/profile/{player_id}")

    async def search_players(self, query: str, type: str = "atp") -> dict:
        """Fetch all players for type and filter by name on the backend."""
        t = type.lower()
        key = cache.make_key("players_list", type=t)
        data = await self._cached(key, CACHE_TTL["search"] * 24, f"{t}/player/")
        # Filter by query string
        players = data if isinstance(data, list) else data.get("data", [])
        q = query.lower().strip()
        filtered = [p for p in players if q in (p.get("name") or "").lower()]
        return {"query": query, "results": filtered}

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


tennis_client = TennisClient()
