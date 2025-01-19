from dataclasses import dataclass
from typing import Optional
from src.openadr_node.config.app_config import ApplicationConfig
from src.openadr_node.models.mqtt_config import MQTTConfig
from src.openadr_node.models.rest_config import RestApiConfig


@dataclass
class HouseNodeConfig:
  """House node specific configuration"""

  node_id: str
  ven_name: str
  vtn_url: str
  openadr_http_host: Optional[str] = 'localhost'
  openadr_http_port: Optional[int] = 8080
  openadr_vtn_path_prefix: Optional[str] = '/0/OpenADR2/Simple/2.0b'
  rest_api_port: int = 5000
  vtn_name: Optional[str] = None
  mqtt_config: Optional[MQTTConfig] = None
  rest_api_config: Optional[RestApiConfig] = None

  def to_application_config(self) -> ApplicationConfig:
    return ApplicationConfig(
      node_id=self.node_id,
      vtn_name=self.vtn_name,
      ven_name=self.ven_name,
      vtn_url=self.vtn_url,
      openadr_http_host=self.openadr_http_host,
      openadr_http_port=self.openadr_http_port,
      openadr_vtn_path_prefix=self.openadr_vtn_path_prefix,
      mqtt_config=self.mqtt_config,
      rest_api_config=self.rest_api_config or RestApiConfig(port=self.rest_api_port),
    )
