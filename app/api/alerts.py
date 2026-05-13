from fastapi import APIRouter, Query

from app.services import alert_service

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


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
            "device_id": a.device_id,
            "alert_type": a.alert_type,
            "strength": a.strength,
            "duration_sec": a.duration_sec,
            "timestamp": a.timestamp,
            "notified": a.notified,
        }
        for a in alerts
    ]
