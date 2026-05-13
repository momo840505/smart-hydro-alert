from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, StrictBool

DEVICE_ID_RE = r"^[a-zA-Z0-9_-]{1,32}$"


class AlertType(StrEnum):
    WATER_RUNNING_NO_HUMAN = "WATER_RUNNING_NO_HUMAN"


class AlertStrength(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DeviceStatusEnum(StrEnum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"


class _StrictBase(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)


class SensorPayload(_StrictBase):
    device_id: str = Field(pattern=DEVICE_ID_RE)
    timestamp: int = Field(ge=0)
    water_flow: StrictBool
    human_present: StrictBool
    running_duration_sec: int = Field(ge=0)
    flow_rate_lpm: float | None = Field(default=None, ge=0)


class AlertPayload(_StrictBase):
    device_id: str = Field(pattern=DEVICE_ID_RE)
    timestamp: int = Field(ge=0)
    alert_type: AlertType
    duration_sec: int = Field(ge=300)
    strength: AlertStrength


class StatusPayload(_StrictBase):
    device_id: str = Field(pattern=DEVICE_ID_RE)
    timestamp: int = Field(ge=0)
    status: DeviceStatusEnum
    uptime_sec: int = Field(ge=0)
    free_heap: int | None = Field(default=None, ge=0)
    rssi: int | None = Field(default=None, le=0)
    firmware_version: str | None = None


class DeviceRegisterRequest(_StrictBase):
    device_id: str = Field(pattern=DEVICE_ID_RE)
    location: str = Field(min_length=1, max_length=64)


def compute_strength(duration_sec: int) -> AlertStrength:
    if duration_sec >= 1200:
        return AlertStrength.HIGH
    if duration_sec >= 600:
        return AlertStrength.MEDIUM
    return AlertStrength.LOW
