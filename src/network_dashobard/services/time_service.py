from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import Optional

import logging

from src.network_dashobard.services.services import ITimeService


class TimeService(ITimeService):
  def __init__(self, timezone_offset: int = 1):
    """Initialize with timezone offset (default: CET = UTC+1)"""
    self.timezone_offset = timezone(timedelta(hours=timezone_offset))

  def convert_timestamp(self, timestamp: int) -> int:
    """Converts Unix timestamp from UTC to timezone-aware milliseconds"""
    try:
      # Create UTC datetime
      utc_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
      # Convert to configured timezone
      local_dt = utc_dt.astimezone(self.timezone_offset)
      # Convert to milliseconds
      return int(local_dt.timestamp() * 1000)
    except Exception as e:
      logging.error(f'Error converting timestamp {timestamp}: {e}')
      return timestamp * 1000  # Return unconverted milliseconds as fallback

  def parse_datetime(self, time_str: str, tz_info: Optional[str] = None) -> datetime:
    """Parses a time string to a datetime object"""
    today_str = datetime.now().strftime('%Y-%m-%d')
    timestamp_str = f'{today_str}T{time_str}:00'
    try:
      dt = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')
      if tz_info:
        dt = dt.replace(tzinfo=ZoneInfo(tz_info))
      return dt
    except ValueError as e:
      logging.error(f'Invalid time string: {time_str}. Error: {e}')
      raise
