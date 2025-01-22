from dataclasses import dataclass
from typing import Optional, Callable

from openleadr import OpenADRServer


@dataclass
class VirtualTopNodeConfig:
  vtn_id: str = ('vtn_id',)
  http_port: Optional[int] = (8080,)
  http_host: Optional[str] = ('0.0.0.0',)
  path_prefix: Optional[str] = None
  server_factory: Callable[..., OpenADRServer] = OpenADRServer
