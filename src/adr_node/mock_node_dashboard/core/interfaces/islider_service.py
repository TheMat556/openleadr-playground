# src/core/interfaces/slider_service.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime


class ISliderService(ABC):
  @abstractmethod
  def load_values(self) -> List[int]:
    """Load slider values from storage"""
    pass

  @abstractmethod
  def save_values(self, values: Any) -> None:
    """Save slider values to storage"""
    pass

  @abstractmethod
  def interpolate_values(self, values: List[int]) -> pd.DataFrame:
    """Interpolate slider values to 15-minute intervals"""
    pass

  @abstractmethod
  def get_current_allowed_consumption(self) -> float:
    """Get current allowed consumption based on slider values"""
    pass

  @abstractmethod
  def get_time_series_data(self) -> Dict[datetime, float]:
    """Get complete time series data for the current day"""
    pass
