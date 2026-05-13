from typing import Annotated

from beanie import Document, Indexed
from pydantic import Field

from app.database.collections import DEVICES


class Device(Document):
    device_id: Annotated[str, Indexed(unique=True)]
    location: str | None = None
    status: str = "OFFLINE"

    last_seen: int | None = None
    uptime_sec: int | None = None
    firmware_version: str | None = None

    water_flow: bool | None = None
    human_present: bool | None = None
    running_duration_sec: int | None = None

    active_alert_at: int | None = Field(
        default=None,
        description="Unix epoch sec when active alert started; None means no active alert",
    )

    created_at: int

    class Settings:
        name = DEVICES
