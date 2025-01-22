from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass
class Interval:
  dtstart: datetime
  duration: timedelta
  signal_payload: Any

  def __post_init__(self) -> None:
    if self.dtstart.tzinfo is None:
      raise ValueError('dtstart must be timezone-aware')

    if self.duration.total_seconds() < 0:
      raise ValueError('duration cannot be negative')
