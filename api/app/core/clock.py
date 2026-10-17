from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from api.app.core.config import settings


def local_now() -> datetime:
    """Return the current time in the application's configured calendar timezone."""
    return datetime.now(ZoneInfo(settings.app_timezone))


def local_today() -> date:
    """Return the calendar date used to group daily check-ins."""
    return local_now().date()


def utc_now_naive() -> datetime:
    """Return a UTC timestamp compatible with Excel's timezone-naive cells."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
