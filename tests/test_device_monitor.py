from unittest.mock import AsyncMock

import pytest

from app.services import device_service
from app.services.device_service import is_device_stale


def test_device_is_online_when_recently_seen():
    assert (
        is_device_stale(
            last_seen=970,
            offline_after_sec=60,
            now=1000,
        )
        is False
    )


def test_device_is_still_online_at_exact_timeout():
    assert (
        is_device_stale(
            last_seen=940,
            offline_after_sec=60,
            now=1000,
        )
        is False
    )


def test_device_is_offline_after_timeout():
    assert (
        is_device_stale(
            last_seen=939,
            offline_after_sec=60,
            now=1000,
        )
        is True
    )


def test_device_without_last_seen_is_stale():
    assert (
        is_device_stale(
            last_seen=None,
            offline_after_sec=60,
            now=1000,
        )
        is True
    )


class FakeDevice:
    def __init__(
        self,
        device_id: str,
        status: str,
        last_seen: int | None,
    ):
        self.device_id = device_id
        self.status = status
        self.last_seen = last_seen
        self.save = AsyncMock()


@pytest.mark.asyncio
async def test_stale_online_device_is_marked_offline(monkeypatch):
    device = FakeDevice(
        device_id="device01",
        status="ONLINE",
        last_seen=900,
    )

    monkeypatch.setattr(
        device_service,
        "list_devices",
        AsyncMock(return_value=[device]),
    )

    monkeypatch.setattr(
        device_service,
        "is_device_stale",
        lambda last_seen, offline_after_sec: True,
    )

    result = await device_service.mark_stale_devices_offline(60)

    assert device.status == "OFFLINE"
    device.save.assert_awaited_once()
    assert result == ["device01"]


@pytest.mark.asyncio
async def test_recent_online_device_stays_online(monkeypatch):
    device = FakeDevice(
        device_id="device01",
        status="ONLINE",
        last_seen=990,
    )

    monkeypatch.setattr(
        device_service,
        "list_devices",
        AsyncMock(return_value=[device]),
    )

    monkeypatch.setattr(
        device_service,
        "is_device_stale",
        lambda last_seen, offline_after_sec: False,
    )

    result = await device_service.mark_stale_devices_offline(60)

    assert device.status == "ONLINE"
    device.save.assert_not_awaited()
    assert result == []


@pytest.mark.asyncio
async def test_already_offline_device_is_ignored(monkeypatch):
    device = FakeDevice(
        device_id="device01",
        status="OFFLINE",
        last_seen=800,
    )

    monkeypatch.setattr(
        device_service,
        "list_devices",
        AsyncMock(return_value=[device]),
    )

    result = await device_service.mark_stale_devices_offline(60)

    assert device.status == "OFFLINE"
    device.save.assert_not_awaited()
    assert result == []
