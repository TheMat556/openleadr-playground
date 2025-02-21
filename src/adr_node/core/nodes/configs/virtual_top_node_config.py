from dataclasses import dataclass
from typing import Optional, Callable

from openleadr import OpenADRServer


@dataclass
class VirtualTopNodeConfig:
  """
  Configuration for a Virtual Top Node (VTN).

  Attributes
  ----------
  vtn_id : str
      The ID of the Virtual Top Node.
  http_port : Optional[int]
      The HTTP port for the VTN server.
  http_host : Optional[str]
      The HTTP host for the VTN server.
  path_prefix : Optional[str]
      The path prefix for the VTN server.
  server_factory : Callable[..., OpenADRServer]
      Factory function to create an OpenADRServer instance.
  """

  vtn_id: str = 'vtn_id'
  http_port: Optional[int] = 8080
  http_host: Optional[str] = '0.0.0.0'
  path_prefix: Optional[str] = None
  server_factory: Callable[..., OpenADRServer] = OpenADRServer
