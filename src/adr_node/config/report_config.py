from dataclasses import field, dataclass
from datetime import timedelta
from typing import Optional, Callable, Any, Dict

from openleadr import enums


@dataclass
class ReportConfig:
  """
  Configuration for the report.

  This class holds the configuration details required for generating reports.

  Attributes
  ----------
  resource_id : str
      The ID of the resource.
  measurement : str
      The type of measurement.
  sampling_rate : timedelta
      The rate at which samples are taken.
  callback : Optional[Callable[[], Any]]
      The callback function to be called for each sample.
  additional_metadata : Dict[str, Any]
      Additional metadata for the report.
  report_type : Optional[enums.REPORT_TYPE]
      The type of the report.
  reading_type : Optional[enums.READING_TYPE]
      The type of reading.
  """

  resource_id: str
  measurement: str
  sampling_rate: timedelta
  callback: Optional[Callable[[], Any]] = None
  additional_metadata: Dict[str, Any] = field(default_factory=dict)
  report_type: Optional[enums.REPORT_TYPE] = None
  reading_type: Optional[enums.READING_TYPE] = None

  def __post_init__(self) -> None:
    """
    Post-initialization processing.

    Raises
    ------
    ValueError
        If the sampling_rate is not positive.
    """
    if self.sampling_rate.total_seconds() <= 0:
      raise ValueError('sampling_rate must be positive')
