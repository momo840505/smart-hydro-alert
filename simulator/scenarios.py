import asyncio
import logging
import random

from simulator.config import SimulatorConfig
from simulator.publisher import (
    mqtt_client,
    now_epoch,
    publish_sensor,
    publish_status,
)

logger = logging.getLogger(__name__)


async def scenario_leak(
    config: SimulatorConfig,
    device_id: str,
    location: str,
    duration_sec: int = 360,
    tick_sec: float = 1.0,
) -> None:
    """Water flowing, no human, for `duration_sec` seconds.

    Backend should fire an alert at running_duration_sec == 300 (5 min).
    Use duration >= 310 to comfortably observe the alert.
    """
    logger.info("[leak] device=%s duration=%ds tick=%.2fs", device_id, duration_sec, tick_sec)
    boot = now_epoch()
    async with mqtt_client(config, client_id=f"sim-{device_id}") as client:
        await publish_status(
            client, location=location, device_id=device_id,
            status="ONLINE", uptime_sec=0, firmware_version="sim-1.0.0",
        )
        running = 0
        for _ in range(duration_sec):
            running += 1
            await publish_sensor(
                client, location=location, device_id=device_id,
                water_flow=True, human_present=False,
                running_duration_sec=running, flow_rate_lpm=4.7,
            )
            await asyncio.sleep(tick_sec)

        # cool-down: reset condition so duplicate-alert state clears
        for _ in range(3):
            await publish_sensor(
                client, location=location, device_id=device_id,
                water_flow=False, human_present=False, running_duration_sec=0,
            )
            await asyncio.sleep(tick_sec)
        await publish_status(
            client, location=location, device_id=device_id,
            status="OFFLINE", uptime_sec=now_epoch() - boot,
        )


async def scenario_normal(
    config: SimulatorConfig,
    device_id: str,
    location: str,
    duration_sec: int = 120,
    tick_sec: float = 1.0,
) -> None:
    """Random water_flow, mostly human present. No alert should fire."""
    logger.info("[normal] device=%s duration=%ds tick=%.2fs", device_id, duration_sec, tick_sec)
    boot = now_epoch()
    async with mqtt_client(config, client_id=f"sim-{device_id}") as client:
        await publish_status(
            client, location=location, device_id=device_id,
            status="ONLINE", uptime_sec=0, firmware_version="sim-1.0.0",
        )
        running = 0
        for _ in range(duration_sec):
            water = random.random() < 0.4
            human = random.random() < 0.75
            if water and not human:
                running += 1
            else:
                running = 0
            flow = round(random.uniform(2.0, 8.0), 2) if water else None
            await publish_sensor(
                client, location=location, device_id=device_id,
                water_flow=water, human_present=human,
                running_duration_sec=running, flow_rate_lpm=flow,
            )
            await asyncio.sleep(tick_sec)
        await publish_status(
            client, location=location, device_id=device_id,
            status="OFFLINE", uptime_sec=now_epoch() - boot,
        )


async def scenario_intermittent(
    config: SimulatorConfig,
    device_id: str,
    location: str,
    duration_sec: int = 180,
    tick_sec: float = 1.0,
) -> None:
    """Water cycles on/off; human always present. No alert should fire."""
    logger.info("[intermittent] device=%s duration=%ds tick=%.2fs", device_id, duration_sec, tick_sec)
    boot = now_epoch()
    async with mqtt_client(config, client_id=f"sim-{device_id}") as client:
        await publish_status(
            client, location=location, device_id=device_id,
            status="ONLINE", uptime_sec=0, firmware_version="sim-1.0.0",
        )
        for tick in range(duration_sec):
            water = (tick // 15) % 2 == 0
            human = True
            running = 0
            flow = round(random.uniform(3.0, 6.0), 2) if water else None
            await publish_sensor(
                client, location=location, device_id=device_id,
                water_flow=water, human_present=human,
                running_duration_sec=running, flow_rate_lpm=flow,
            )
            await asyncio.sleep(tick_sec)
        await publish_status(
            client, location=location, device_id=device_id,
            status="OFFLINE", uptime_sec=now_epoch() - boot,
        )


async def scenario_multi(
    config: SimulatorConfig,
    count: int = 3,
    duration_sec: int = 180,
    tick_sec: float = 1.0,
) -> None:
    """Run N devices concurrently. Device 0 = leak, rest = normal."""
    logger.info("[multi] count=%d duration=%ds", count, duration_sec)
    tasks = []
    for i in range(count):
        device_id = f"sim_dev_{i:02d}"
        if i == 0:
            coro = scenario_leak(config, device_id, "bathroom", duration_sec, tick_sec)
        else:
            coro = scenario_normal(config, device_id, f"room_{i}", duration_sec, tick_sec)
        tasks.append(asyncio.create_task(coro, name=f"sim-{device_id}"))
    await asyncio.gather(*tasks)
