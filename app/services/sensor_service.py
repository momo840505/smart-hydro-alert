import logging
import time

from app.models.payloads import SensorPayload
from app.models.sensor import SensorLog

logger = logging.getLogger(__name__)


async def store_log(payload: SensorPayload) -> SensorLog:
    log = SensorLog(
        device_id=payload.device_id,
        timestamp=payload.timestamp,
        water_flow=payload.water_flow,
        human_present=payload.human_present,
        running_duration_sec=payload.running_duration_sec,
        flow_rate_lpm=payload.flow_rate_lpm,
        created_at=int(time.time()),
    )
    await log.insert()
    return log


async def get_history(
    device_id: str,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 100,
) -> list[SensorLog]:
    query = SensorLog.find(SensorLog.device_id == device_id)
    if start_time is not None:
        query = query.find(SensorLog.timestamp >= start_time)
    if end_time is not None:
        query = query.find(SensorLog.timestamp <= end_time)
    return await query.sort(-SensorLog.timestamp).limit(limit).to_list()
