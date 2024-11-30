from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List


@dataclass
class Interval:
  dtstart: datetime
  duration: timedelta
  signal_payload: Any


@dataclass
class EventSignal:
  ven_id: str
  signal_name: str
  signal_type: str
  callback: Callable[[Dict[str, Any]], None]
  intervals: List[Interval] = field(default_factory=list)
