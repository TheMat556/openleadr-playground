from datetime import datetime
from typing import List
from dataclasses import dataclass


@dataclass
class ConsumptionBatchResult:
  """
  Data class for consumption batch result in the OpenADR system.

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
