from datetime import datetime, timezone, timedelta
from typing import Optional

# Indian Standard Time (UTC+5:30)
IST_TIMEZONE = timezone(timedelta(hours=5, minutes=30))

def get_current_ist_time() -> datetime:
    """
    Get current time in Indian Standard Time
    """
    return datetime.now(IST_TIMEZONE)

def convert_to_ist(dt: datetime) -> datetime:
    """
    Convert a datetime object to IST timezone
    If the datetime is naive (no timezone), assume it's in UTC
    """
    if dt.tzinfo is None:
        # If naive datetime, assume UTC
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.astimezone(IST_TIMEZONE)

def format_ist_datetime(dt: Optional[datetime], format_str: str = "%Y-%m-%d %H:%M:%S IST") -> Optional[str]:
    """
    Format a datetime object to IST timezone string
    """
    if dt is None:
        return None
    
    ist_dt = convert_to_ist(dt)
    return ist_dt.strftime(format_str)

def parse_ist_datetime(datetime_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    Parse a datetime string and return IST datetime object
    """
    dt = datetime.strptime(datetime_str, format_str)
    return dt.replace(tzinfo=IST_TIMEZONE)
