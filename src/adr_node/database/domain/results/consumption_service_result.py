from datetime import datetime
from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class ConsumptionServiceResult:
  """
  Data class for consumption service result in the OpenADR system.

  Attributes
  ----------
  success : bool
      Indicates if the service call was successful.
  data : Any
      Data returned by the service.
  error : Optional[str]
      Error message if the service call failed.
  timestamp : datetime
      Timestamp of the service result.
  """

  success: bool
  data: Any = None
  error: Optional[str] = None
  timestamp: datetime = datetime.utcnow()
