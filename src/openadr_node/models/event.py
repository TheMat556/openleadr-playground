from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List


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


@dataclass
class EventSignal:
  ven_id: str
  signal_name: str
  signal_type: str
  callback: Callable[[Dict[str, Any]], None]
  intervals: List[Interval] = field(default_factory=list)
