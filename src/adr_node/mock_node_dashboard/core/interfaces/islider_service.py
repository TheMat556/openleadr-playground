from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

import numpy as np


class ISliderService(ABC):
  """
  Interface for slider service.

  This interface defines the methods required for a slider service, including loading and saving values,
  interpolating values, and retrieving consumption data.

  Methods
  -------
  load_values() -> List[int]
      Load slider values from storage.
  save_values(values: Any) -> None
      Save slider values to storage.
  interpolate_values(values: List[int]) -> Dict[str, np.ndarray]
      Interpolate slider values to 15-minute intervals.
  get_current_allowed_consumption() -> float
      Get current allowed consumption based on slider values.
  get_time_series_data() -> Dict[datetime, float]
      Get complete time series data for the current day.
  """

  @abstractmethod
  def load_values(self) -> List[int]:
    """
    Load slider values from storage.

    :return: A list of slider values.
    :rtype: List[int]
    """
    pass

  @abstractmethod
  def save_values(self, values: Any) -> None:
    """
    Save slider values to storage.

    :param values: The slider values to save.
    :type values: Any
    """
    pass

  @abstractmethod
  def interpolate_values(self, values: List[int]) -> Dict[str, np.ndarray]:
    """
    Interpolate slider values to 15-minute intervals.

    :param values: A list of slider values.
    :type values: List[int]
    :return: A dictionary with interpolated values.
    :rtype: Dict[str, np.ndarray]
    """
    pass

  @abstractmethod
  def get_current_allowed_consumption(self) -> float:
    """
    Get current allowed consumption based on slider values.

    :return: The current allowed consumption.
    :rtype: float
    """
    pass

  @abstractmethod
  def get_time_series_data(self) -> Dict[datetime, float]:
    """
    Get complete time series data for the current day.

    :return: A dictionary with time series data.
    :rtype: Dict[datetime, float]
    """
    pass
