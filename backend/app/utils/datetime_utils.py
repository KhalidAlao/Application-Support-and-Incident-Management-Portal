from datetime import datetime, timezone

def utc_now():
    """Return current UTC datetime with timezone awareness."""
    return datetime.now(timezone.utc)