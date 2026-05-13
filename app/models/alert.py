from typing import Annotated

from beanie import Document, Indexed

from app.database.collections import ALERTS


class Alert(Document):
    device_id: Annotated[str, Indexed()]
    alert_type: str
    strength: str
    duration_sec: int
    timestamp: Annotated[int, Indexed()]
    created_at: int
    notified: bool = False

    class Settings:
        name = ALERTS
