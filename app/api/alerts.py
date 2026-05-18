from fastapi import APIRouter, Query

from app.services import alert_service

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def as01(value: int | bool | None) -> int:
    return 1 if value in (1, True) else 0


@router.get("")
async def list_alerts(
    device_id: str | None = Query(default=None),
    start_time: int | None = Query(default=None, ge=0),
    end_time: int | None = Query(default=None, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[dict]:
    alerts = await alert_service.list_alerts(device_id, start_time, end_time, limit)

    return [
        {
            "device_id": alert.device_id,
            "alert_type": alert.alert_type,
            "status": alert.alert_type,
            "strength": alert.strength,
            "duration_sec": alert.duration_sec,
            "timestamp": alert.timestamp,
            "notified": as01(alert.notified),
        }
        for alert in alerts
    ]