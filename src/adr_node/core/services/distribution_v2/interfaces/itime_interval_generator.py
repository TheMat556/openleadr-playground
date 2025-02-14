# src/adr_node/core/services/distribution/interfaces/itime_interval_generator.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class ITimeIntervalGenerator(ABC):
  @abstractmethod
  def generate_intervals(self) -> List[Dict[str, Any]]:
    pass
