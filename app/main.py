"""
Tennis Hub - FastAPI Backend
Port 5004
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime
import logging

from app.tennis_client import tennis_client
from app.cache import cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Tennis Hub starting on port 5004")
    cache.cleanup()
    yield
    await tennis_client.close()
    logger.info("Tennis Hub stopped")


app = FastAPI(title="Tennis Hub", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ---- HTML ----

@app.get("/", response_class=HTMLResponse)
async def root():
    index = TEMPLATES_DIR / "index.html"
    return HTMLResponse(content=index.read_text(encoding="utf-8"))


# ---- Health ----

@app.get("/api/health")
async def health():
    stats = cache.stats()
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat(), "cache": stats}


# ---- Rankings ----

@app.get("/api/rankings")
async def get_rankings(type: str = Query("atp", pattern="^(atp|wta)$")):
    """ATP or WTA rankings."""
    try:
        data = await tennis_client.get_rankings(type)
        return {"type": type, "data": data}
    except Exception as e:
        logger.error("Rankings error: %s", e)
        raise HTTPException(status_code=502, detail=str(e))


# ---- Results ----

@app.get("/api/results")
async def get_results(date: str = Query(None, description="YYYY-MM-DD")):
    """Match results for a given date."""
    try:
        data = await tennis_client.get_results(date)
        return {"date": date, "data": data}
    except Exception as e:
        logger.error("Results error: %s", e)
        raise HTTPException(status_code=502, detail=str(e))


# ---- Calendar ----

@app.get("/api/calendar")
async def get_calendar():
    """Upcoming tournaments."""
    try:
        data = await tennis_client.get_calendar()
        return {"data": data}
    except Exception as e:
        logger.error("Calendar error: %s", e)
        raise HTTPException(status_code=502, detail=str(e))


# ---- H2H ----

@app.get("/api/h2h")
async def get_h2h(p1: int = Query(..., description="Player 1 ID"),
                  p2: int = Query(..., description="Player 2 ID")):
    """Head-to-head between two players."""
    try:
        data = await tennis_client.get_h2h(p1, p2)
        return {"player1_id": p1, "player2_id": p2, "data": data}
    except Exception as e:
        logger.error("H2H error: %s", e)
        raise HTTPException(status_code=502, detail=str(e))


# ---- Draws ----

@app.get("/api/draws")
async def get_draws(tournament: int = Query(..., description="Tournament ID")):
    """Tournament draw/bracket."""
    try:
        data = await tennis_client.get_draws(tournament)
        return {"tournament_id": tournament, "data": data}
    except Exception as e:
        logger.error("Draws error: %s", e)
        raise HTTPException(status_code=502, detail=str(e))


# ---- Player ----

@app.get("/api/player")
async def get_player(id: int = Query(..., description="Player ID")):
    """Player profile and stats."""
    try:
        data = await tennis_client.get_player(id)
        return {"player_id": id, "data": data}
    except Exception as e:
        logger.error("Player error: %s", e)
        raise HTTPException(status_code=502, detail=str(e))


# ---- Search ----

@app.get("/api/search")
async def search(q: str = Query(..., min_length=2, description="Search query")):
    """Search for players or tournaments."""
    try:
        data = await tennis_client.search_players(q)
        return {"query": q, "data": data}
    except Exception as e:
        logger.error("Search error: %s", e)
        raise HTTPException(status_code=502, detail=str(e))


# ---- Cache admin ----

@app.delete("/api/cache")
async def clear_cache():
    """Clear expired cache entries."""
    removed = cache.cleanup()
    return {"removed": removed, "stats": cache.stats()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5004)
