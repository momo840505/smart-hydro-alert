from app.models.payloads import SensorPayload
from app.services.alert_service import has_reset, is_abnormal


def _payload(water: bool, human: bool, duration: int) -> SensorPayload:
    return SensorPayload(
        device_id="device01",
        timestamp=1778926532,
        water_flow=water,
        human_present=human,
        running_duration_sec=duration,
    )


class TestIsAbnormal:
    def test_below_threshold(self):
        assert not is_abnormal(_payload(True, False, 299), 300)

    def test_at_threshold(self):
        assert is_abnormal(_payload(True, False, 300), 300)

    def test_above_threshold(self):
        assert is_abnormal(_payload(True, False, 600), 300)

    def test_water_off(self):
        assert not is_abnormal(_payload(False, False, 600), 300)

    def test_human_present(self):
        assert not is_abnormal(_payload(True, True, 600), 300)


class TestHasReset:
    def test_water_off_resets(self):
        assert has_reset(_payload(False, False, 0))

    def test_human_present_resets(self):
        assert has_reset(_payload(True, True, 0))

    def test_abnormal_does_not_reset(self):
        assert not has_reset(_payload(True, False, 600))
