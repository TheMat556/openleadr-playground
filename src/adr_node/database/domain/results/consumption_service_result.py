from datetime import datetime
from typing import Optional, Any
from dataclasses import dataclass


# Service Data Models
@dataclass
class ConsumptionServiceResult:
  success: bool
  data: Any = None
  error: Optional[str] = None
  timestamp: datetime = datetime.utcnow()
