import json
import logging
import time

from pydantic import ValidationError

from app.core.config import Settings
from app.models.payloads import AlertPayload, SensorPayload, StatusPayload
from app.mqtt.topics import device_id_from_topic, topic_kind
from app.services import alert_service, device_service, sensor_service
from app.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)


def _validate_timestamp(ts: int, settings: Settings) -> bool:
    now = int(time.time())
    return (now - settings.timestamp_skew_past_sec) <= ts <= (now + settings.timestamp_skew_future_sec)


def _validate_topic_match(topic: str, device_id: str) -> bool:
    expected = device_id_from_topic(topic)
    return expected == device_id


async def handle_message(topic: str, raw: bytes, settings: Settings) -> None:
    if len(raw) > settings.mqtt_max_payload_bytes:
        logger.warning("payload too large: topic=%s size=%d", topic, len(raw))
        return

    kind = topic_kind(topic)
    if kind is None:
        logger.debug("unknown topic, ignoring: %s", topic)
        return

    try:
        body = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning("invalid JSON on %s: %s", topic, e)
        return

    try:
        if kind == "sensor":
            payload = SensorPayload.model_validate(body)
            if not _validate_topic_match(topic, payload.device_id):
                logger.warning("topic/device_id mismatch on %s: %s", topic, payload.device_id)
                return
            if not _validate_timestamp(payload.timestamp, settings):
                logger.warning("timestamp out of skew window: %s ts=%d", topic, payload.timestamp)
                return
            await _handle_sensor(payload, settings)

        elif kind == "alert":
            payload_a = AlertPayload.model_validate(body)
            if not _validate_topic_match(topic, payload_a.device_id):
                logger.warning("topic/device_id mismatch on %s", topic)
                return
            if not _validate_timestamp(payload_a.timestamp, settings):
                logger.warning("alert timestamp out of skew window: %s", topic)
                return
            await _handle_alert(payload_a, settings)

        elif kind == "status":
            payload_s = StatusPayload.model_validate(body)
            if not _validate_topic_match(topic, payload_s.device_id):
                logger.warning("topic/device_id mismatch on %s", topic)
                return
            if not _validate_timestamp(payload_s.timestamp, settings):
                logger.warning("status timestamp out of skew window: %s", topic)
                return
            await _handle_status(payload_s)

    except ValidationError as e:
        logger.warning("schema validation failed on %s: %s", topic, e.errors())


async def _handle_sensor(payload: SensorPayload, settings: Settings) -> None:
    device = await device_service.touch_from_sensor(payload)
    await sensor_service.store_log(payload)
    await alert_service.evaluate_sensor(payload, device, settings)
    await ws_manager.broadcast(
        payload.device_id,
        {
            "event": "sensor_update",
            "data": {
                "device_id": payload.device_id,
                "timestamp": payload.timestamp,
                "water_flow": payload.water_flow,
                "human_present": payload.human_present,
                "running_duration_sec": payload.running_duration_sec,
                "flow_rate_lpm": payload.flow_rate_lpm,
            },
        },
    )


async def _handle_alert(payload: AlertPayload, settings: Settings) -> None:
    device = await device_service._get_or_create(payload.device_id)
    await alert_service.ingest_alert_topic(payload, device, settings)


async def _handle_status(payload: StatusPayload) -> None:
    await device_service.apply_status(payload)
    await ws_manager.broadcast(
        payload.device_id,
        {
            "event": "device_status",
            "data": {
                "device_id": payload.device_id,
                "status": payload.status.value,
                "uptime_sec": payload.uptime_sec,
                "timestamp": payload.timestamp,
            },
        },
    )
