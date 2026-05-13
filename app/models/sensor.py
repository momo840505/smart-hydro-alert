from typing import Annotated

from beanie import Document, Indexed

from app.database.collections import SENSOR_LOGS


class SensorLog(Document):
    device_id: Annotated[str, Indexed()]
    timestamp: Annotated[int, Indexed()]
    water_flow: bool
    human_present: bool
    running_duration_sec: int
    flow_rate_lpm: float | None = None
    created_at: int

    class Settings:
        name = SENSOR_LOGS
