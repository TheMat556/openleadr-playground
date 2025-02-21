from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass
class Interval:
  """
  Represents a time interval with a start time, duration, and associated signal payload.

  Attributes
  ----------
  dtstart : datetime
      The start time of the interval. Must be timezone-aware.
  duration : timedelta
      The duration of the interval. Must be non-negative.
  signal_payload : Any
      The payload associated with the interval.
  """

  dtstart: datetime
  duration: timedelta
  signal_payload: Any

  def __post_init__(self) -> None:
    """
    Validate the interval attributes after initialization.

    Raises
    ------
    ValueError
        If dtstart is not timezone-aware or if duration is negative.
    """
    if self.dtstart.tzinfo is None:
      raise ValueError('dtstart must be timezone-aware')

    if self.duration.total_seconds() < 0:
      raise ValueError('duration cannot be negative')
