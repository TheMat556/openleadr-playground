# src/adr_node/core/services/distribution/interfaces/itime_interval_generator.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class ITimeIntervalGenerator(ABC):
  """
  Interface for Time Interval Generator in the OpenADR system.

  This interface defines the method to generate time intervals for the ADR system.

  Methods
  -------
  generate_intervals() -> List[Dict[str, Any]]
      Generate time intervals.
  """

  @abstractmethod
  def generate_intervals(self) -> List[Dict[str, Any]]:
    """
    Generate time intervals for the ADR system.

    Returns
    -------
    List[Dict[str, Any]]
        List of dictionaries containing interval start time, duration, and signal payload.
    """
    pass
