from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ZValueBatchResult:
  """Result of batch z-value operations."""

  successful_records: int
  failed_records: int
  errors: List[str]
