from dataclasses import dataclass
from typing import Optional
from ..models.mqtt_config import MQTTConfig
from ..models.rest_config import RestApiConfig


@dataclass
class ApplicationConfig:
  """Application-wide configuration"""

  node_id: Optional[str] = None
  vtn_name: Optional[str] = None
  ven_name: Optional[str] = None
  vtn_url: Optional[str] = None
  openadr_http_host: Optional[str] = None
  openadr_http_port: Optional[int] = None
  openadr_vtn_path_prefix: Optional[str] = None
  mqtt_config: Optional[MQTTConfig] = None
  rest_api_config: Optional[RestApiConfig] = None
