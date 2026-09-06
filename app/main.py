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
from app.services import device_service
from app.services.websocket_manager import ws_manager


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


async def monitor_device_connections(settings) -> None:
    log = logging.getLogger("app.device_monitor")

    while True:
        offline_device_ids = await device_service.mark_stale_devices_offline(
            settings.device_offline_after_sec
        )

        for device_id in offline_device_ids:
            await ws_manager.broadcast(
                device_id,
                {
                    "event": "device_status",
                    "data": {
                        "device_id": device_id,
                        "status": "OFFLINE",
                    },
                },
            )

            log.info(
                "offline update sent for device %s",
                device_id,
            )

        await asyncio.sleep(settings.device_status_check_interval_sec)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    _configure_logging(settings.log_level)

    log = logging.getLogger("app.lifespan")

    await init_db(settings)

    mqtt_task = asyncio.create_task(
        run_subscriber(settings),
        name="mqtt-subscriber",
    )

    device_monitor_task = asyncio.create_task(
        monitor_device_connections(settings),
        name="device-monitor",
    )

    log.info("backend startup complete")

    try:
        yield

    finally:
        log.info("shutting down")

        mqtt_task.cancel()
        device_monitor_task.cancel()

        for task in (
            mqtt_task,
            device_monitor_task,
        ):
            try:
                await task
            except asyncio.CancelledError:
                pass

        close_db()

        log.info("shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict:
        return {
            "status": "ok",
            "app": settings.app_name,
            "env": settings.app_env,
        }

    app.include_router(devices_router.router)
    app.include_router(alerts_router.router)
    app.include_router(ws_router.router)

    # The Docker image serves the built React app from this directory.
    frontend_dist = os.getenv("FRONTEND_DIST_DIR")

    if frontend_dist and Path(frontend_dist).is_dir():
        app.mount(
            "/",
            StaticFiles(
                directory=frontend_dist,
                html=True,
            ),
            name="frontend",
        )

    return app


app = create_app()
