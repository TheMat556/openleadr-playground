from dataclasses import dataclass
from typing import Optional


@dataclass
class ConsumptionData:
  timestamp: int
  ven_id: str
  resource_id: str
  value: float
  created_at: Optional[int]
  updated_at: Optional[int]
