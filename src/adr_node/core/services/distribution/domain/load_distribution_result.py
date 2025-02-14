from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime


@dataclass(frozen=True)
class LoadDistributionResult:
  success: bool
  data: Optional[Dict[str, List[Dict[str, Any]]]]
  error: Optional[str] = None
  timestamp: datetime = datetime.utcnow()
