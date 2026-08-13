import pytest
from datetime import datetime, timezone, timedelta
from backend.app.utils import ensure_utc


class TestEnsureUTC:
    def test_naive_datetime_becomes_utc_aware(self):
        """Naive datetime should be assumed UTC and given timezone."""
        naive = datetime(2026, 8, 13, 10, 0, 0)
        aware = ensure_utc(naive)
        assert aware.tzinfo == timezone.utc
        assert aware == datetime(2026, 8, 13, 10, 0, 0, tzinfo=timezone.utc)

    def test_utc_aware_datetime_unchanged(self):
        """Already UTC-aware datetime should remain unchanged."""
        aware = datetime(2026, 8, 13, 10, 0, 0, tzinfo=timezone.utc)
        result = ensure_utc(aware)
        assert result is aware
        assert result.tzinfo == timezone.utc

    def test_non_utc_aware_datetime_converted(self):
        """Non-UTC timezone (e.g., EST) should be converted to UTC."""
        est = timezone(timedelta(hours=-4))
        aware_est = datetime(2026, 8, 13, 6, 0, 0, tzinfo=est)  # 6 AM EST = 10 AM UTC
        result = ensure_utc(aware_est)
        assert result.tzinfo == timezone.utc
        assert result == datetime(2026, 8, 13, 10, 0, 0, tzinfo=timezone.utc)