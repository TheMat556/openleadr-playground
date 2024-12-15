from dataclasses import field, dataclass
from datetime import timedelta
from typing import Optional, Callable, Any, Dict


@dataclass
class ReportConfiguration:
  resource_id: str
  measurement: str
  sampling_rate: timedelta
  callback: Optional[Callable[[], Any]] = None
  additional_metadata: Dict[str, Any] = field(default_factory=dict)

  def __post_init__(self) -> None:
    if self.sampling_rate.total_seconds() <= 0:
      raise ValueError('sampling_rate must be positive')
