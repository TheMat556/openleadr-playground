from datetime import datetime
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ZValueBatchResult:
  """
  Result of batch z-value operations.

  Attributes
  ----------
  successful_records : int
      Number of successful records in the batch.
  failed_records : int
      Number of failed records in the batch.
  errors : List[str]
      List of error messages.
  timestamp : datetime
      Timestamp of the batch result.
  """

  successful_records: int
  failed_records: int
  errors: List[str]
  timestamp: datetime = datetime.utcnow()
