from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

def get_ist_now() -> datetime:
    """Get current datetime in IST."""
    return datetime.now(ZoneInfo("Asia/Kolkata"))

def utc_to_ist(utc_dt: datetime) -> datetime:
    """Convert UTC datetime to IST."""
    if utc_dt.tzinfo is None:  # if it's naive, assume it's UTC
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(ZoneInfo("Asia/Kolkata"))

def ist_to_utc(ist_dt: datetime) -> datetime:
    """Convert IST datetime to UTC."""
    if ist_dt.tzinfo is None:  # if it's naive, assume it's IST
        ist_dt = ist_dt.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
    return ist_dt.astimezone(timezone.utc)

def format_ist_date(dt: datetime) -> str:
    """Format datetime in IST for display."""
    ist_dt = utc_to_ist(dt)
    return ist_dt.strftime("%B %d, %Y")

def get_ist_date(dt: datetime) -> datetime:
    """Get just the date part in IST timezone."""
    ist_dt = utc_to_ist(dt)
    return ist_dt.date()