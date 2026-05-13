import logging
import time

from app.models.device import Device
from app.models.payloads import DeviceRegisterRequest, SensorPayload, StatusPayload

logger = logging.getLogger(__name__)


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
    logger.info("device registered: %s @ %s", device.device_id, device.location)
    return device


async def _get_or_create(device_id: str) -> Device:
    device = await get_device(device_id)
    if device:
        return device
    device = Device(device_id=device_id, status="OFFLINE", created_at=int(time.time()))
    await device.insert()
    return device


async def touch_from_sensor(payload: SensorPayload) -> Device:
    device = await _get_or_create(payload.device_id)
    device.status = "ONLINE"
    device.last_seen = payload.timestamp
    device.water_flow = payload.water_flow
    device.human_present = payload.human_present
    device.running_duration_sec = payload.running_duration_sec
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
