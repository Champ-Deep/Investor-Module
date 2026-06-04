from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request) -> dict:
    db_ok = False
    try:
        async with request.app.state.pool.acquire() as conn:
            db_ok = (await conn.fetchval("SELECT 1")) == 1
    except Exception:
        db_ok = False
    return {"status": "ok", "db": db_ok}


@router.get("/status")
async def status(request: Request) -> dict:
    """Which live modes are active (no secrets leaked) — so you can confirm a key took effect."""
    settings = request.app.state.settings
    firms_loaded = 0
    try:
        async with request.app.state.pool.acquire() as conn:
            firms_loaded = await conn.fetchval("SELECT count(*) FROM firm")
    except Exception:
        firms_loaded = 0
    return {
        "llm_parse": settings.llm_parse_provider,  # openrouter | heuristic
        "llm_model": settings.llm_model if settings.openrouter_api_key else None,
        "embeddings": settings.embeddings_provider,  # openai | deterministic
        "data_source": settings.active_data_source,  # seed | lakeb2b
        "contact_sla_days": settings.contact_sla_days,
        "firms_loaded": firms_loaded,
    }
