from fastapi import APIRouter, HTTPException, Query, status

from app.models.payloads import DeviceRegisterRequest
from app.services import device_service, sensor_service

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("")
async def list_devices() -> list[dict]:
    devices = await device_service.list_devices()
    return [
        {
            "device_id": d.device_id,
            "location": d.location,
            "status": d.status,
            "last_seen": d.last_seen,
            "has_active_alert": d.active_alert_at is not None,
        }
        for d in devices
    ]


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_device(req: DeviceRegisterRequest) -> dict:
    device = await device_service.register_device(req)
    return {
        "device_id": device.device_id,
        "location": device.location,
        "status": device.status,
        "created_at": device.created_at,
    }


@router.get("/{device_id}/live")
async def get_live(device_id: str) -> dict:
    device = await device_service.get_device(device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="device not found")
    return {
        "device_id": device.device_id,
        "location": device.location,
        "status": device.status,
        "water_flow": device.water_flow,
        "human_present": device.human_present,
        "running_duration_sec": device.running_duration_sec,
        "last_seen": device.last_seen,
        "uptime_sec": device.uptime_sec,
        "firmware_version": device.firmware_version,
        "has_active_alert": device.active_alert_at is not None,
    }


@router.get("/{device_id}/history")
async def get_history(
    device_id: str,
    start_time: int | None = Query(default=None, ge=0),
    end_time: int | None = Query(default=None, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[dict]:
    logs = await sensor_service.get_history(device_id, start_time, end_time, limit)
    return [
        {
            "timestamp": log.timestamp,
            "water_flow": log.water_flow,
            "human_present": log.human_present,
            "running_duration_sec": log.running_duration_sec,
            "flow_rate_lpm": log.flow_rate_lpm,
        }
        for log in logs
    ]
