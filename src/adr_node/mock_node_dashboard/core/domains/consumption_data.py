# src/core/models/consumption_data.py
from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime


@dataclass
class ConsumptionData:
  timestamp: int
  total_consumption: float
  unit: str
  ven_count: int
  statistics: Dict[str, Any]

  @staticmethod
  def from_dict(data: Dict[str, Any]) -> 'ConsumptionData':
    return ConsumptionData(
      timestamp=data['timestamp'],
      total_consumption=data['total_consumption'],
      unit=data['unit'],
      ven_count=data['ven_count'],
      statistics=data['statistics'],
    )

  def get_datetime(self) -> datetime:
    return datetime.fromtimestamp(self.timestamp / 1000)
