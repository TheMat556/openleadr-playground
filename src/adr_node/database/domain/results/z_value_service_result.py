from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any


@dataclass(frozen=True)
class ZValueServiceResult:
  """Result of z-value service operations."""

  success: bool
  data: Optional[Any] = None
  error: Optional[str] = None
  timestamp: datetime = datetime.utcnow()
