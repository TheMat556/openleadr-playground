from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any


@dataclass
class ApiResponse:
  status: str
  timestamp: datetime
  data: Optional[Any] = None
  error: Optional[str] = None
