import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "app": settings.app_name, "env": settings.app_env}

    app.include_router(devices_router.router)
    app.include_router(alerts_router.router)
    app.include_router(ws_router.router)
    return app


app = create_app()
