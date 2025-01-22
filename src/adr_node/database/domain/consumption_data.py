from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ConsumptionData:
  timestamp: int
  ven_id: str
  resource_id: str
  value: float
  created_at: datetime = datetime.utcnow()
  updated_at: Optional[datetime] = None
