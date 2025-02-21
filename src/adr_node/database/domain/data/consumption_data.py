from dataclasses import dataclass
from typing import Optional

from openleadr import enums


@dataclass
class ConsumptionData:
  """
  Data class for consumption data in the OpenADR system.

  Attributes
  ----------
  timestamp : int
      Timestamp of the consumption data.
  ven_id : str
      VEN ID associated with the consumption data.
  resource_id : str
      Resource ID associated with the consumption data.
  value : float
      Consumption value.
  created_at : Optional[int]
      Timestamp when the data was created.
  updated_at : Optional[int]
      Timestamp when the data was last updated.
  report_type : Optional[enums.REPORT_TYPE]
      Type of the report.
  reading_type : Optional[enums.READING_TYPE]
      Type of the reading.
  """

  timestamp: int
  ven_id: str
  resource_id: str
  value: float
  created_at: Optional[int]
  updated_at: Optional[int]
  report_type: Optional[enums.REPORT_TYPE] = None
  reading_type: Optional[enums.READING_TYPE] = None
