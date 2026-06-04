import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from cadence.api.routes import firms, freshness, health, search
from cadence.config import get_settings
from cadence.db.pool import create_pool

API_PREFIX = "/api"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    try:
        app.state.pool = await create_pool(settings)
    except Exception:
        # Listen-first: never block boot on a slow/unready DB. /api/health stays live (db:false)
        # and the deploy passes its healthcheck; DB errors surface on data routes instead.
        app.state.pool = None
    try:
        yield
    finally:
        if app.state.pool is not None:
            await app.state.pool.close()


class _SPAStaticFiles(StaticFiles):
    """Serve the built SPA, falling back to index.html for client-side routes (deep links)."""

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404:
                return await super().get_response("index.html", scope)
            raise


def create_app() -> FastAPI:
    app = FastAPI(title="Cadence API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],  # dev; prod is same-origin (SPA served below)
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for router in (health.router, search.router, firms.router, freshness.router):
        app.include_router(router, prefix=API_PREFIX)

    # In production the built SPA is mounted at / (single service). In local dev FRONTEND_DIST is
    # unset and Vite serves the frontend, proxying /api here.
    dist = os.environ.get("FRONTEND_DIST", "")
    if dist and Path(dist).is_dir():
        app.mount("/", _SPAStaticFiles(directory=dist, html=True), name="spa")

    return app


app = create_app()
