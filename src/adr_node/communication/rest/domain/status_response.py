from dataclasses import dataclass
from datetime import datetime


@dataclass
class StatusResponse:
  """
  Represents the status response of a node.

  Attributes
  ----------
  node_id : str
      The unique identifier of the node.
  status : str
      The current status of the node.
  last_updated : datetime
      The timestamp of the last update.
  uptime : float
      The uptime of the node in seconds.
  version : str
      The version of the node software.
  """

  node_id: str
  status: str
  last_updated: datetime
  uptime: float
  version: str
