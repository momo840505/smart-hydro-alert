import logging
import time

from app.core.config import Settings
from app.models.alert import Alert
from app.models.device import Device
from app.models.payloads import (
    AlertPayload,
    AlertType,
    SensorPayload,
    compute_strength,
)
from app.services import notification_service
from app.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)


def is_abnormal(payload: SensorPayload, threshold_sec: int) -> bool:
    return (
        payload.water_flow
        and not payload.human_present
        and payload.running_duration_sec >= threshold_sec
    )


def has_reset(payload: SensorPayload) -> bool:
    return (not payload.water_flow) or payload.human_present


async def _persist_and_dispatch(
    device_id: str,
    duration_sec: int,
    timestamp: int,
    settings: Settings,
) -> Alert:
    alert = Alert(
        device_id=device_id,
        alert_type=AlertType.WATER_RUNNING_NO_HUMAN.value,
        strength=compute_strength(duration_sec).value,
        duration_sec=duration_sec,
        timestamp=timestamp,
        created_at=int(time.time()),
    )
    await alert.insert()
    logger.info(
        "alert created: device=%s duration=%ds strength=%s",
        device_id, duration_sec, alert.strength,
    )

    notified = await notification_service.send_alert_notification(alert, settings)
    if notified:
        alert.notified = True
        await alert.save()

    await ws_manager.broadcast(
        device_id,
        {
            "event": "alert_created",
            "data": {
                "device_id": alert.device_id,
                "alert_type": alert.alert_type,
                "strength": alert.strength,
                "duration_sec": alert.duration_sec,
                "timestamp": alert.timestamp,
            },
        },
    )
    return alert


async def evaluate_sensor(payload: SensorPayload, device: Device, settings: Settings) -> Alert | None:
    """Apply alert rule + duplicate prevention to a sensor reading."""
    if is_abnormal(payload, settings.alert_duration_threshold_sec):
        if device.active_alert_at is not None:
            return None
        alert = await _persist_and_dispatch(
            payload.device_id, payload.running_duration_sec, payload.timestamp, settings,
        )
        device.active_alert_at = payload.timestamp
        await device.save()
        return alert

    if has_reset(payload) and device.active_alert_at is not None:
        device.active_alert_at = None
        await device.save()
        logger.info("alert reset for device=%s", payload.device_id)
    return None


async def ingest_alert_topic(payload: AlertPayload, device: Device, settings: Settings) -> Alert | None:
    """Handle alert published directly by ESP32. Same duplicate-prevention path."""
    if device.active_alert_at is not None:
        logger.debug("ignoring ESP32-published alert; already active for device=%s", payload.device_id)
        return None
    alert = await _persist_and_dispatch(
        payload.device_id, payload.duration_sec, payload.timestamp, settings,
    )
    device.active_alert_at = payload.timestamp
    await device.save()
    return alert


async def list_alerts(
    device_id: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 100,
) -> list[Alert]:
    query = Alert.find()
    if device_id is not None:
        query = query.find(Alert.device_id == device_id)
    if start_time is not None:
        query = query.find(Alert.timestamp >= start_time)
    if end_time is not None:
        query = query.find(Alert.timestamp <= end_time)
    return await query.sort(-Alert.timestamp).limit(limit).to_list()
