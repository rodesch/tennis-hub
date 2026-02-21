"""
TennisApi1 client with aggressive caching to stay within free tier limits.
Every method checks cache first; only calls API on cache miss.
"""

import httpx
import logging
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
        """ATP or WTA rankings. type: 'atp' | 'wta'"""
        key = cache.make_key("rankings", type=type)
        return await self._cached(key, CACHE_TTL["rankings"], f"rankings/{type.upper()}")

    async def get_results(self, date: str = None) -> dict:
        """Recent match results. date: YYYY-MM-DD (defaults to today)."""
        from datetime import date as dt
        d = date or dt.today().isoformat()
        key = cache.make_key("results", date=d)
        return await self._cached(key, CACHE_TTL["results"], "results", {"date": d})

    async def get_calendar(self) -> dict:
        """Upcoming tournaments calendar."""
        key = cache.make_key("calendar")
        return await self._cached(key, CACHE_TTL["calendar"], "competitions")

    async def get_h2h(self, player1_id: int, player2_id: int) -> dict:
        """Head-to-head between two players."""
        key = cache.make_key("h2h", p1=player1_id, p2=player2_id)
        return await self._cached(
            key, CACHE_TTL["h2h"], "h2h",
            {"playerId1": player1_id, "playerId2": player2_id}
        )

    async def get_draws(self, tournament_id: int) -> dict:
        """Tournament draw/bracket."""
        key = cache.make_key("draws", tid=tournament_id)
        return await self._cached(key, CACHE_TTL["draws"], f"competition/{tournament_id}/draw")

    async def get_player(self, player_id: int) -> dict:
        """Player profile and stats."""
        key = cache.make_key("player", pid=player_id)
        return await self._cached(key, CACHE_TTL["player"], f"player/{player_id}")

    async def search_players(self, query: str) -> dict:
        """Search for players or tournaments."""
        key = cache.make_key("search", q=query.lower().strip())
        return await self._cached(key, CACHE_TTL["search"], "search", {"query": query})

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


tennis_client = TennisClient()
