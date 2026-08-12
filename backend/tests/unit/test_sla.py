import pytest
from datetime import datetime, timezone, timedelta
from backend.app.utils.sla import calculate_sla_deadlines


class TestCalculateSLADeadlines:
    """Pure unit tests for SLA calculation – no Flask, no DB, no fixtures."""

    def test_p1_priority(self):
        """P1: 60 min response, 240 min resolution."""
        start = datetime(2026, 8, 12, 10, 0, 0, tzinfo=timezone.utc)
        response_due, resolve_due = calculate_sla_deadlines(60, 240, start)

        expected_response = datetime(2026, 8, 12, 11, 0, 0, tzinfo=timezone.utc)
        expected_resolve = datetime(2026, 8, 12, 14, 0, 0, tzinfo=timezone.utc)

        assert response_due == expected_response
        assert resolve_due == expected_resolve

    def test_zero_minutes(self):
        """Edge case: zero minutes – deadlines equal start_time."""
        start = datetime(2026, 8, 12, 10, 0, 0, tzinfo=timezone.utc)
        response_due, resolve_due = calculate_sla_deadlines(0, 0, start)

        assert response_due == start
        assert resolve_due == start

    def test_naive_datetime_raises_error(self):
        """Naive datetime (no tzinfo) must raise ValueError."""
        naive_start = datetime(2026, 8, 12, 10, 0, 0)  # no tzinfo

        with pytest.raises(ValueError) as exc_info:
            calculate_sla_deadlines(60, 240, naive_start)

        assert "timezone-aware" in str(exc_info.value)
        assert "UTC" in str(exc_info.value)

    def test_p4_priority(self):
        """P4: 480 min response, 2880 min resolution (48 hours)."""
        start = datetime(2026, 8, 12, 10, 0, 0, tzinfo=timezone.utc)
        response_due, resolve_due = calculate_sla_deadlines(480, 2880, start)

        expected_response = datetime(2026, 8, 12, 18, 0, 0, tzinfo=timezone.utc)
        expected_resolve = datetime(2026, 8, 14, 10, 0, 0, tzinfo=timezone.utc)   # 48 hours = 2 days

        assert response_due == expected_response
        assert resolve_due == expected_resolve