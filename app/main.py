import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import alerts as alerts_router
from app.api import devices as devices_router
from app.api import websocket as ws_router
from app.core.config import get_settings
from app.database.mongodb import close_db, init_db
from app.mqtt.client import run_subscriber


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    _configure_logging(settings.log_level)
    log = logging.getLogger("app.lifespan")

    await init_db(settings)
    mqtt_task = asyncio.create_task(run_subscriber(settings), name="mqtt-subscriber")
    log.info("backend startup complete")

    try:
        yield
    finally:
        log.info("shutting down")
        mqtt_task.cancel()
        try:
            await mqtt_task
        except asyncio.CancelledError:
            pass
        close_db()
        log.info("shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    # IMPORTANT: allow_origins=["*"] must never be combined with
    # allow_credentials=True. Starlette's CORSMiddleware reflects the
    # request's actual Origin header back when the origin list is "*" and
    # credentials are allowed, which means literally any website could
    # make credentialed requests to this API from a victim's browser.
    # Settings.cors_allowed_origins_list is an explicit allowlist instead
    # (see app/core/config.py) -- add real dashboard origins there via the
    # CORS_ALLOWED_ORIGINS env var, don't widen this back to "*".
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "app": settings.app_name, "env": settings.app_env}

    app.include_router(devices_router.router)
    app.include_router(alerts_router.router)
    app.include_router(ws_router.router)

    # Serve the built React dashboard, if present. This mount MUST come after every
    # API router above -- StaticFiles(html=True) mounted at "/" would otherwise
    # shadow them. FRONTEND_DIST_DIR is unset in local dev / docker-compose (the
    # separate nginx "frontend" service or `npm run dev` serves the dashboard there
    # instead) and set to /app/frontend_dist by the Docker image (see ../Dockerfile),
    # so this mount is a no-op except in the built container. html=True serves
    # frontend_dist/index.html both for "/" and as the fallback for any unmatched
    # path, which is what lets the SPA's client-side routing work on refresh.
    frontend_dist = os.getenv("FRONTEND_DIST_DIR")
    if frontend_dist and Path(frontend_dist).is_dir():
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

    return app


app = create_app()
