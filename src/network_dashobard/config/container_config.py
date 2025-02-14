from dataclasses import dataclass
from typing import Optional


@dataclass
class ContainerConfig:
  container_name: str
  rest_api_port: int
  layer: int
  VTN_URL: Optional[str] = None
  node_id: Optional[str] = None
