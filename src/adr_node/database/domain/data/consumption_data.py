from dataclasses import dataclass
from typing import Optional

from openleadr import enums


@dataclass
class ConsumptionData:
  timestamp: int
  ven_id: str
  resource_id: str
  value: float
  created_at: Optional[int]
  updated_at: Optional[int]
  report_type: Optional[enums.REPORT_TYPE] = None
  reading_type: Optional[enums.READING_TYPE] = None
