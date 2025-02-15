from dataclasses import field, dataclass
from datetime import timedelta
from typing import Optional, Callable, Any, Dict


@dataclass
class ReportConfiguration:
  """
  Configuration for a report.

  Attributes
  ----------
  resource_id : str
      The ID of the resource.
  measurement : str
      The type of measurement.
  sampling_rate : timedelta
      The sampling rate for the report. Must be positive.
  callback : Optional[Callable[[], Any]]
      The callback function for the report.
  additional_metadata : Dict[str, Any]
      Additional metadata for the report.
  """

  resource_id: str
  measurement: str
  sampling_rate: timedelta
  callback: Optional[Callable[[], Any]] = None
  additional_metadata: Dict[str, Any] = field(default_factory=dict)

  def __post_init__(self) -> None:
    """
    Validate the report configuration attributes after initialization.

    Raises
    ------
    ValueError
        If sampling_rate is not positive.
    """
    if self.sampling_rate.total_seconds() <= 0:
      raise ValueError('sampling_rate must be positive')
