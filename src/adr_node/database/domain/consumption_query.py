from dataclasses import dataclass
from typing import Optional


@dataclass
class ConsumptionQuery:
  timestamp_start: Optional[int] = None
  timestamp_end: Optional[int] = None
  ven_id: Optional[str] = None
  resource_id: Optional[str] = None
  limit: int = 100
  offset: int = 0
  order_by: str = 'timestamp'
  order_direction: str = 'DESC'
