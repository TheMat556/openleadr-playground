from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any


@dataclass
class NodeStatus:
  node_id: str
  status: str
  last_updated: datetime
  uptime: float
  version: str


@dataclass
class ApiResponse:
  status: str
  timestamp: datetime
  data: Optional[Any] = None
  message: Optional[str] = None
