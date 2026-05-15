import logging
import time

from app.core.config import Settings
from app.models.alert import Alert
from app.models.device import Device
from app.models.payloads import (
    AlertPayload,
    AlertStrength,
    ConditionStatus,
    SensorPayload,
    compute_strength,
    derive_condition_status,
    should_notify_user,
)
from app.services import notification_service
from app.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)


def _strength_for_status(status: ConditionStatus, duration_sec: int) -> AlertStrength:
    if status == ConditionStatus.CRITICAL:
        return AlertStrength.HIGH
    return compute_strength(duration_sec)


def is_abnormal(payload: SensorPayload, threshold_sec: int) -> bool:
    status = derive_condition_status(payload, threshold_sec)
    return should_notify_user(status)


def has_reset(payload: SensorPayload, threshold_sec: int) -> bool:
    status = derive_condition_status(payload, threshold_sec)
    return not should_notify_user(status)


async def _persist_and_dispatch(
    device_id: str,
    condition_status: ConditionStatus,
    duration_sec: int,
    timestamp: int,
    settings: Settings,
) -> Alert:
    alert = Alert(
        device_id=device_id,
        alert_type=condition_status.value,
        strength=_strength_for_status(condition_status, duration_sec).value,
        duration_sec=duration_sec,
        timestamp=timestamp,
        created_at=int(time.time()),
    )
    await alert.insert()

    logger.info(
        "alert created: device=%s status=%s duration=%ds strength=%s",
        device_id,
        condition_status.value,
        duration_sec,
        alert.strength,
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
                "status": condition_status.value,
                "strength": alert.strength,
                "duration_sec": alert.duration_sec,
                "timestamp": alert.timestamp,
                "notified": 1 if alert.notified else 0,
            },
        },
    )

    return alert


async def evaluate_sensor(
    payload: SensorPayload,
    device: Device,
    settings: Settings,
) -> Alert | None:
    condition_status = derive_condition_status(
        payload,
        settings.alert_duration_threshold_sec,
    )

    if should_notify_user(condition_status):
        if (
            device.active_alert_at is not None
            and device.active_alert_status == condition_status.value
        ):
            return None

        alert = await _persist_and_dispatch(
            payload.device_id,
            condition_status,
            payload.running_duration_sec,
            payload.timestamp,
            settings,
        )

        device.active_alert_at = payload.timestamp
        device.active_alert_status = condition_status.value
        await device.save()

        return alert

    if has_reset(payload, settings.alert_duration_threshold_sec) and device.active_alert_at is not None:
        device.active_alert_at = None
        device.active_alert_status = None
        await device.save()
        logger.info("alert reset for device=%s", payload.device_id)

    return None


async def ingest_alert_topic(
    payload: AlertPayload,
    device: Device,
    settings: Settings,
) -> Alert | None:
    condition_status = (
        ConditionStatus.CRITICAL
        if payload.alert_type.value == ConditionStatus.CRITICAL.value
        else ConditionStatus.ALERT
    )

    if (
        device.active_alert_at is not None
        and device.active_alert_status == condition_status.value
    ):
        logger.debug(
            "ignoring ESP32-published alert; already active for device=%s",
            payload.device_id,
        )
        return None

    alert = await _persist_and_dispatch(
        payload.device_id,
        condition_status,
        payload.duration_sec,
        payload.timestamp,
        settings,
    )

    device.active_alert_at = payload.timestamp
    device.active_alert_status = condition_status.value
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