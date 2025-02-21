from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any


@dataclass(frozen=True)
class ZValueServiceResult:
  """
  Result of z-value service operations.

  Attributes
  ----------
  success : bool
      Indicates if the service call was successful.
  data : Optional[Any]
      Data returned by the service.
  error : Optional[str]
      Error message if the service call failed.
  timestamp : datetime
      Timestamp of the service result.
  """

  success: bool
  data: Optional[Any] = None
  error: Optional[str] = None
  timestamp: datetime = datetime.utcnow()
