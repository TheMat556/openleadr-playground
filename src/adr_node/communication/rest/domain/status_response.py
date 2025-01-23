from dataclasses import dataclass
from datetime import datetime


@dataclass
class StatusResponse:
  node_id: str
  status: str
  last_updated: datetime
  uptime: float
  version: str
