from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime


@dataclass
class ConsumptionData:
  """
  Data class for consumption data.

  :param timestamp: The timestamp of the data in milliseconds since epoch.
  :type timestamp: int
  :param total_consumption: The total consumption value.
  :type total_consumption: float
  :param unit: The unit of the consumption value.
  :type unit: str
  :param ven_count: The count of virtual energy nodes.
  :type ven_count: int
  :param statistics: Additional statistics related to the consumption data.
  :type statistics: Dict[str, Any]
  """

  timestamp: int
  total_consumption: float
  unit: str
  ven_count: int
  statistics: Dict[str, Any]

  @staticmethod
  def from_dict(data: Dict[str, Any]) -> 'ConsumptionData':
    """
    Create a ConsumptionData instance from a dictionary.

    :param data: A dictionary containing consumption data.
    :type data: Dict[str, Any]
    :return: A ConsumptionData instance.
    :rtype: ConsumptionData
    """
    return ConsumptionData(
      timestamp=data['timestamp'],
      total_consumption=data['total_consumption'],
      unit=data['unit'],
      ven_count=data['ven_count'],
      statistics=data['statistics'],
    )

  def get_datetime(self) -> datetime:
    """
    Convert the timestamp to a datetime object.

    :return: A datetime object representing the timestamp.
    :rtype: datetime
    """
    return datetime.fromtimestamp(self.timestamp / 1000)
