from dataclasses import dataclass


@dataclass
class ConsumptionResponse:
  """
  Represents the consumption response of a node.

  Attributes
  ----------
  node_id : str
      The unique identifier of the node.
  value : float
      The consumption value.
  timestamp : int
      The timestamp of the consumption data as a Unix timestamp.
  unit : str, optional
      The unit of the consumption value, default is 'kW'.
  """

  node_id: str
  value: float
  timestamp: int
  unit: str = 'kW'
