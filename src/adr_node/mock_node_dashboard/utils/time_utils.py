# src/utils/time_utils.py
from datetime import datetime, timedelta, timezone
from typing import List, Optional


class TimeUtils:
  @staticmethod
  def generate_hour_labels(count: int = 24) -> List[str]:
    """
    Generate hour labels in 24-hour format.

    Args:
        count: Number of hours to generate labels for

    Returns:
        List of hour labels in HH:00 format
    """
    return [f'{hour:02d}:00' for hour in range(count)]

  @staticmethod
  def get_current_timezone_offset() -> int:
    """
    Get the current timezone offset in hours.

    Returns:
        Timezone offset in hours
    """
    return int(
      datetime.now(timezone.utc).astimezone().utcoffset().total_seconds() / 3600
    )

  @staticmethod
  def round_to_interval(dt: datetime, minutes: int = 15) -> datetime:
    """
    Round a datetime to the nearest interval.

    Args:
        dt: Datetime to round
        minutes: Interval in minutes

    Returns:
        Rounded datetime
    """
    minute = dt.minute
    rounded_minute = (minute // minutes) * minutes
    return dt.replace(minute=rounded_minute, second=0, microsecond=0)

  @staticmethod
  def get_day_boundaries(
    timezone_offset: int = 1, reference_date: Optional[datetime] = None
  ) -> tuple[datetime, datetime]:
    """
    Get the start and end timestamps for a day.

    Args:
        timezone_offset: Timezone offset in hours
        reference_date: Optional reference date, defaults to current date

    Returns:
        Tuple of (start_datetime, end_datetime)
    """
    tz = timezone(timedelta(hours=timezone_offset))
    if reference_date is None:
      reference_date = datetime.now(tz)

    start = reference_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    return start, end

  @staticmethod
  def datetime_to_unix_ms(dt: datetime) -> int:
    """
    Convert datetime to Unix timestamp in milliseconds.

    Args:
        dt: Datetime to convert

    Returns:
        Unix timestamp in milliseconds
    """
    return int(dt.timestamp() * 1000)
