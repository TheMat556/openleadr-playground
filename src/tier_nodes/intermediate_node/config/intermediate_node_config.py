from dataclasses import dataclass
from typing import Optional

from src.adr_node.config.adr_config import AdrConfig
from src.adr_node.config.mqtt_config import MQTTConfig
from src.adr_node.config.rest_api_config import RestApiConfig
from src.adr_node.config.application_config import ApplicationConfig


@dataclass
class IntermediateNodeConfig:
  """
  Intermediate node specific configuration.

  :param adr_config: ADR configuration.
  :type adr_config: AdrConfig
  :param mqtt_config: MQTT configuration.
  :type mqtt_config: Optional[MQTTConfig]
  :param rest_config: REST API configuration.
  :type rest_config: RestApiConfig
  :param ven_name: VEN name.
  :type ven_name: str
  :param vtn_url: VTN URL.
  :type vtn_url: str
  """

  adr_config: AdrConfig
  mqtt_config: Optional[MQTTConfig]
  rest_config: RestApiConfig
  ven_name: str
  vtn_url: str

  def to_application_config(self) -> ApplicationConfig:
    """
    Convert to application configuration.

    :return: Application configuration.
    :rtype: ApplicationConfig
    """
    return ApplicationConfig(
      adr_config=self.adr_config,
      mqtt_config=self.mqtt_config,
      rest_config=self.rest_config,
      energy_control_panel_config=None,
    )
