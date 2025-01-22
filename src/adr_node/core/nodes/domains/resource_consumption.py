from dataclasses import dataclass
from datetime import datetime
from typing import Tuple


@dataclass
class ResourceConsumption:
  ven_id: str
  resource_id: str
  data: Tuple[datetime, float]
