import argparse
import asyncio
import logging
import sys

from simulator.config import load_config
from simulator.scenarios import (
    scenario_intermittent,
    scenario_leak,
    scenario_multi,
    scenario_normal,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="simulator",
        description="Mock ESP32 -> MQTT publisher for testing the FastAPI backend.",
    )
    sub = p.add_subparsers(dest="scenario", required=True)

    single = argparse.ArgumentParser(add_help=False)
    single.add_argument("--device-id", default="device01")
    single.add_argument("--location", default="bathroom")
    single.add_argument("--tick", type=float, default=1.0, help="Seconds between sensor messages")

    leak = sub.add_parser(
        "leak", parents=[single],
        help="Water running, no human -- backend should alert at ~300s",
    )
    leak.add_argument("--duration", type=int, default=360)

    normal = sub.add_parser(
        "normal", parents=[single],
        help="Random usage with human present -- no alert expected",
    )
    normal.add_argument("--duration", type=int, default=120)

    inter = sub.add_parser(
        "intermittent", parents=[single],
        help="On/off water with human present -- no alert expected",
    )
    inter.add_argument("--duration", type=int, default=180)

    multi = sub.add_parser(
        "multi", help="Run N devices concurrently (device 0 = leak, others = normal)",
    )
    multi.add_argument("--count", type=int, default=3)
    multi.add_argument("--duration", type=int, default=180)
    multi.add_argument("--tick", type=float, default=1.0)

    return p.parse_args(argv)


async def _run(args: argparse.Namespace) -> None:
    config = load_config()
    if args.scenario == "leak":
        await scenario_leak(config, args.device_id, args.location, args.duration, args.tick)
    elif args.scenario == "normal":
        await scenario_normal(config, args.device_id, args.location, args.duration, args.tick)
    elif args.scenario == "intermittent":
        await scenario_intermittent(config, args.device_id, args.location, args.duration, args.tick)
    elif args.scenario == "multi":
        await scenario_multi(config, args.count, args.duration, args.tick)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    args = _parse_args()
    try:
        asyncio.run(_run(args))
    except KeyboardInterrupt:
        logging.info("simulator interrupted by user")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
