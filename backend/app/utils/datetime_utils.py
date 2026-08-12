from datetime import datetime, timezone

def utc_now():
    """Return current UTC datetime with timezone awareness."""
    return datetime.now(timezone.utc)

def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure a datetime is timezone-aware UTC.
    If naive, assume it represents UTC and add the timezone.
    If already aware but not UTC, convert to UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    if dt.tzinfo != timezone.utc:
        return dt.astimezone(timezone.utc)
    return dt