from dataclasses import dataclass


@dataclass
class ConsumptionResponse:
  node_id: str
  value: float
  timestamp: int
  unit: str = 'kW'
