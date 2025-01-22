from dataclasses import dataclass
from typing import Callable

from openleadr import OpenADRClient


@dataclass
class VirtualEndNodeConfig:
  ven_name: str
  vtn_url: str
  client_factory: Callable[..., OpenADRClient] = OpenADRClient
