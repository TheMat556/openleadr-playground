from dataclasses import dataclass
from src.adr_node.config.adr_config import AdrConfig
from src.adr_node.config.mqtt_config import MQTTConfig
from src.adr_node.config.rest_api_config import RestApiConfig
from src.adr_node.config.application_config import ApplicationConfig


@dataclass
class HouseNodeConfig:
  """House node specific configuration"""

  adr_config: AdrConfig
  mqtt_config: MQTTConfig
  rest_config: RestApiConfig

  def to_application_config(self) -> ApplicationConfig:
    return ApplicationConfig(
      adr_config=self.adr_config,
      mqtt_config=self.mqtt_config,
      rest_config=self.rest_config,
    )
