from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class ApiResponse:
  """
  Represents a generic API response.

  Attributes
  ----------
  status : str
      The status of the API response.
  timestamp : str
      The timestamp of the response.
  data : Optional[Any], optional
      The data returned by the API, default is None.
  error : Optional[str], optional
      The error message if any, default is None.
  """

  status: str
  timestamp: str
  data: Optional[Any] = None
  error: Optional[str] = None
