from dataclasses import dataclass
from typing import List


@dataclass
class ConsumptionBatchResult:
  success_count: int
  failed_count: int
  errors: List[str]
