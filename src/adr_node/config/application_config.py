from dataclasses import dataclass
from typing import Optional

from src.adr_node.config.adr_config import AdrConfig
from src.adr_node.config.mqtt_config import MQTTConfig
from src.adr_node.config.rest_api_config import RestApiConfig


@dataclass
class ApplicationConfig:
  adr_config: AdrConfig
  mqtt_config: Optional[MQTTConfig]
  rest_config: RestApiConfig
  pass
