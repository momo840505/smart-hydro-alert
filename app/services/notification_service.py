import logging

import httpx

from app.core.config import Settings
from app.models.alert import Alert

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def _format_message(alert: Alert) -> str:
    return (
        "[Smart Hydro Alert]\n"
        f"Device: {alert.device_id}\n"
        f"Status: {alert.alert_type}\n"
        f"Severity: {alert.strength}\n"
        f"Duration: {alert.duration_sec}s\n"
        "Action: Please check the tap or nearby water area."
    )


async def send_alert_notification(alert: Alert, settings: Settings) -> bool:
    token = settings.telegram_bot_token
    chat_id = settings.telegram_chat_id

    if not token or not chat_id:
        logger.debug("telegram not configured; skipping notification")
        return False

    url = _TELEGRAM_API.format(token=token)
    payload = {
        "chat_id": chat_id,
        "text": _format_message(alert),
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

        logger.info("telegram notification sent for alert device=%s", alert.device_id)
        return True

    except httpx.HTTPError as error:
        logger.warning("telegram send failed: %s", error)
        return False