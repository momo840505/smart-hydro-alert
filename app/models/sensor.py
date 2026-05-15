from typing import Annotated

from beanie import Document, Indexed

from app.database.collections import SENSOR_LOGS


class SensorLog(Document):
    device_id: Annotated[str, Indexed()]
    timestamp: Annotated[int, Indexed()]

    water_flow: int
    human_present: int
    water_detected: int = 0
    alert: int = 0
    status: str | None = None

    running_duration_sec: int = 0
    flow_rate_lpm: float | None = None

    created_at: int

    class Settings:
        name = SENSOR_LOGS