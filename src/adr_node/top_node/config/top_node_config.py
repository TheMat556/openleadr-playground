from dataclasses import dataclass
from typing import Optional

from src.adr_node.config.adr_config import AdrConfig
from src.adr_node.config.mqtt_config import MQTTConfig
from src.adr_node.config.rest_api_config import RestApiConfig
from src.adr_node.config.application_config import ApplicationConfig
from src.adr_node.mock_node_dashboard.config.app_config import EnergyControlPanelConfig


@dataclass
class TopNodeConfig:
  """House node specific configuration"""

  adr_config: AdrConfig
  energy_control_panel_config: Optional[EnergyControlPanelConfig]
  mqtt_config: Optional[MQTTConfig]
  rest_config: RestApiConfig

  def to_application_config(self) -> ApplicationConfig:
    return ApplicationConfig(
      adr_config=self.adr_config,
      energy_control_panel_config=self.energy_control_panel_config,
      mqtt_config=self.mqtt_config,
      rest_config=self.rest_config,
    )
