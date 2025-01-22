from dataclasses import dataclass
from typing import Optional


@dataclass
class AdrConfig:
  node_id: Optional[str] = None
  vtn_name: Optional[str] = None
  ven_name: Optional[str] = None
  vtn_url: Optional[str] = None
  openadr_http_host: Optional[str] = None
  openadr_http_port: Optional[int] = None
  openadr_vtn_path_prefix: Optional[str] = None
