import logging

import httpx

from app.core.config import Settings
from app.models.alert import Alert

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def _format_message(alert: Alert) -> str:
    """Create a maintenance-friendly Telegram alert message.

    ALERT:
    - measurable water flow continues without nearby human presence.

    CRITICAL:
    - measurable water flow and FC-37 water contact are detected together.
    """

    if alert.alert_type == "CRITICAL":
        risk_level = "HIGH"
        duration_text = "Immediate trigger"
        reason = (
            "Measurable water flow and FC-37 water contact were detected "
            "at the same time."
        )
        action = "Please inspect the sink, tap, and nearby floor area immediately."

    elif alert.alert_type == "ALERT":
        risk_level = "MEDIUM"
        duration_text = f"{alert.duration_sec}s"
        reason = (
            "Water flow continued without nearby human presence until the "
            "alert threshold was reached."
        )
        action = "Please check whether the tap has been left running."

    else:
        risk_level = alert.strength
        duration_text = f"{alert.duration_sec}s"
        reason = "Abnormal water-related condition detected."
        action = "Please check the monitored restroom area."

    return (
        "🚨 Smart Hydro Alert\n\n"
        f"Device: {alert.device_id}\n"
        f"Status: {alert.alert_type}\n"
        f"Risk Level: {risk_level}\n"
        f"Duration: {duration_text}\n\n"
        f"Reason:\n{reason}\n\n"
        f"Action:\n{action}"
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