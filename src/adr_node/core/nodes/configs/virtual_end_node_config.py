from dataclasses import dataclass
from typing import Callable

from openleadr import OpenADRClient


@dataclass
class VirtualEndNodeConfig:
  """
  Configuration for a Virtual End Node (VEN).

  Attributes
  ----------
  ven_name : str
      The name of the Virtual End Node.
  vtn_url : str
      The URL of the Virtual Top Node (VTN).
  client_factory : Callable[..., OpenADRClient]
      Factory function to create an OpenADRClient instance.
  """

  ven_name: str
  vtn_url: str
  client_factory: Callable[..., OpenADRClient] = OpenADRClient
