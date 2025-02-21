from dataclasses import dataclass
from datetime import datetime
from typing import Tuple


@dataclass
class ResourceConsumption:
  """
  Represents the resource consumption data for a Virtual End Node (VEN).

  Attributes
  ----------
  ven_id : str
      The ID of the Virtual End Node.
  resource_id : str
      The ID of the resource being consumed.
  data : Tuple[datetime, float]
      A tuple containing the timestamp and the consumption value.
  """

  ven_id: str
  resource_id: str
  data: Tuple[datetime, float]
