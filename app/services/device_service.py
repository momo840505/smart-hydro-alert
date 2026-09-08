import logging
import time

from app.models.device import Device
from app.models.payloads import (
    DeviceRegisterRequest,
    SensorPayload,
    StatusPayload,
    derive_condition_status,
    expected_alert_value,
)

logger = logging.getLogger(__name__)


def is_device_stale(
    last_seen: int | None,
    offline_after_sec: int,
    now: int | None = None,
) -> bool:
    if last_seen is None:
        return True

    current_time = int(time.time()) if now is None else now

    return current_time - last_seen > offline_after_sec


async def get_device(device_id: str) -> Device | None:
    return await Device.find_one(Device.device_id == device_id)


async def list_devices() -> list[Device]:
    return await Device.find_all().sort(Device.device_id).to_list()


async def register_device(req: DeviceRegisterRequest) -> Device:
    existing = await get_device(req.device_id)

    if existing:
        existing.location = req.location
        await existing.save()
        return existing

    device = Device(
        device_id=req.device_id,
        location=req.location,
        status="OFFLINE",
        created_at=int(time.time()),
    )

    await device.insert()
    return device


async def _get_or_create(device_id: str) -> Device:
    device = await get_device(device_id)

    if device:
        return device

    device = Device(
        device_id=device_id,
        status="OFFLINE",
        created_at=int(time.time()),
    )

    await device.insert()
    return device


def _needs_duration_timer(payload: SensorPayload) -> bool:
    return payload.water_flow == 1 and payload.human_present == 0 and payload.water_detected == 0


def _calculate_running_duration(
    payload: SensorPayload,
    device: Device,
    time_scale: int = 1,
) -> int:
    """Calculate unattended-flow duration.

    MQTT/device traffic uses the default 1x scale. The REST demo endpoint can
    pass a larger scale so the UI reaches the five-minute alert threshold
    without changing how real device messages are handled.
    """
    if time_scale < 1:
        raise ValueError("time_scale must be at least 1")

    if not _needs_duration_timer(payload):
        device.abnormal_started_at = None
        return 0

    if device.abnormal_started_at is None:
        device.abnormal_started_at = payload.timestamp

    elapsed_real_sec = max(0, payload.timestamp - device.abnormal_started_at)
    scaled_duration = elapsed_real_sec * time_scale

    return max(payload.running_duration_sec, scaled_duration)


async def touch_from_sensor(
    payload: SensorPayload,
    threshold_sec: int,
    time_scale: int = 1,
) -> Device:
    device = await _get_or_create(payload.device_id)

    payload.running_duration_sec = _calculate_running_duration(
        payload,
        device,
        time_scale=time_scale,
    )

    condition_status = derive_condition_status(payload, threshold_sec)
    alert_value = expected_alert_value(condition_status)

    device.status = "ONLINE"
    device.condition_status = condition_status.value
    device.last_seen = payload.timestamp

    device.water_flow = payload.water_flow
    device.human_present = payload.human_present
    device.water_detected = payload.water_detected
    device.alert = alert_value
    device.running_duration_sec = payload.running_duration_sec
    device.flow_rate_lpm = payload.flow_rate_lpm

    await device.save()
    return device


async def reset_device_to_normal(device_id: str) -> Device:
    now = int(time.time())
    device = await _get_or_create(device_id)

    device.status = "ONLINE"
    device.condition_status = "NORMAL"
    device.last_seen = now

    device.water_flow = 0
    device.human_present = 0
    device.water_detected = 0
    device.alert = 0
    device.running_duration_sec = 0
    device.flow_rate_lpm = 0

    device.abnormal_started_at = None
    device.active_alert_at = None
    device.active_alert_status = None

    await device.save()
    return device


async def apply_status(payload: StatusPayload) -> Device:
    device = await _get_or_create(payload.device_id)

    device.status = payload.status.value
    device.last_seen = payload.timestamp
    device.uptime_sec = payload.uptime_sec

    if payload.firmware_version is not None:
        device.firmware_version = payload.firmware_version

    await device.save()
    return device


async def mark_stale_devices_offline(
    offline_after_sec: int,
) -> list[str]:
    devices = await list_devices()

    offline_device_ids: list[str] = []

    for device in devices:
        if device.status != "ONLINE":
            continue

        if not is_device_stale(
            device.last_seen,
            offline_after_sec,
        ):
            continue

        device.status = "OFFLINE"
        await device.save()

        offline_device_ids.append(device.device_id)

        logger.info(
            "device marked offline: %s",
            device.device_id,
        )

    return offline_device_ids
