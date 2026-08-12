from datetime import datetime, timedelta

def calculate_sla_deadlines(response_minutes: int, resolution_minutes: int, start_time: datetime) -> tuple[datetime, datetime]:
    """
    Pure function: compute initial SLA deadlines from priority minutes and a start time.

    Does NOT account for hold-time pausing — that's a separate concern handled
    by the service layer when recalculating deadlines after an On Hold period.

    Raises ValueError if start_time is naive (no tzinfo).
    """
    if start_time.tzinfo is None:
        raise ValueError("start_time must be timezone-aware (UTC)")

    response_due = start_time + timedelta(minutes=response_minutes)
    resolve_due = start_time + timedelta(minutes=resolution_minutes)

    return response_due, resolve_due