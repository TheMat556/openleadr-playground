from datetime import datetime
from typing import List
from dataclasses import dataclass


@dataclass
class ConsumptionBatchResult:
  successful_records: int
  failed_records: int
  errors: List[str]
  timestamp: datetime = datetime.utcnow()
