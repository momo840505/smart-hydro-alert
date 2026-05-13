import pytest
from pydantic import ValidationError

from app.models.payloads import (
    AlertPayload,
    AlertStrength,
    AlertType,
    DeviceStatusEnum,
    SensorPayload,
    StatusPayload,
    compute_strength,
)


class TestSensorPayload:
    def test_valid_minimum(self):
        p = SensorPayload(
            device_id="device01",
            timestamp=1778926532,
            water_flow=True,
            human_present=False,
            running_duration_sec=287,
        )
        assert p.flow_rate_lpm is None

    def test_valid_with_flow_rate(self):
        p = SensorPayload(
            device_id="device01",
            timestamp=1778926532,
            water_flow=True,
            human_present=False,
            running_duration_sec=0,
            flow_rate_lpm=4.7,
        )
        assert p.flow_rate_lpm == 4.7

    def test_rejects_bad_device_id(self):
        with pytest.raises(ValidationError):
            SensorPayload(
                device_id="bad id!",
                timestamp=1778926532,
                water_flow=True,
                human_present=False,
                running_duration_sec=0,
            )

    def test_rejects_negative_duration(self):
        with pytest.raises(ValidationError):
            SensorPayload(
                device_id="device01",
                timestamp=1778926532,
                water_flow=True,
                human_present=False,
                running_duration_sec=-1,
            )

    def test_rejects_string_boolean(self):
        with pytest.raises(ValidationError):
            SensorPayload(
                device_id="device01",
                timestamp=1778926532,
                water_flow="true",
                human_present=False,
                running_duration_sec=0,
            )


class TestAlertPayload:
    def test_valid(self):
        a = AlertPayload(
            device_id="device01",
            timestamp=1778926833,
            alert_type=AlertType.WATER_RUNNING_NO_HUMAN,
            duration_sec=301,
            strength=AlertStrength.HIGH,
        )
        assert a.alert_type == AlertType.WATER_RUNNING_NO_HUMAN

    def test_rejects_short_duration(self):
        with pytest.raises(ValidationError):
            AlertPayload(
                device_id="device01",
                timestamp=1778926833,
                alert_type=AlertType.WATER_RUNNING_NO_HUMAN,
                duration_sec=299,
                strength=AlertStrength.HIGH,
            )

    def test_rejects_unknown_alert_type(self):
        with pytest.raises(ValidationError):
            AlertPayload(
                device_id="device01",
                timestamp=1778926833,
                alert_type="UNKNOWN_TYPE",
                duration_sec=301,
                strength=AlertStrength.LOW,
            )


class TestStatusPayload:
    def test_online(self):
        s = StatusPayload(
            device_id="device01",
            timestamp=1778926532,
            status=DeviceStatusEnum.ONLINE,
            uptime_sec=15420,
        )
        assert s.status == DeviceStatusEnum.ONLINE

    def test_rssi_must_be_non_positive(self):
        with pytest.raises(ValidationError):
            StatusPayload(
                device_id="device01",
                timestamp=1778926532,
                status=DeviceStatusEnum.ONLINE,
                uptime_sec=10,
                rssi=5,
            )


class TestComputeStrength:
    @pytest.mark.parametrize(
        "duration, expected",
        [
            (300, AlertStrength.LOW),
            (599, AlertStrength.LOW),
            (600, AlertStrength.MEDIUM),
            (1199, AlertStrength.MEDIUM),
            (1200, AlertStrength.HIGH),
            (9999, AlertStrength.HIGH),
        ],
    )
    def test_bucketing(self, duration, expected):
        assert compute_strength(duration) == expected
