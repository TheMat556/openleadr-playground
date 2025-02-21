from dataclasses import dataclass
from typing import Optional

from src.adr_node.config.adr_config import AdrConfig
from src.adr_node.config.mqtt_config import MQTTConfig
from src.adr_node.config.rest_api_config import RestApiConfig
from src.adr_node.mock_node_dashboard.config.app_config import EnergyControlPanelConfig


@dataclass
class ApplicationConfig:
  """
  Configuration for the application.

  This class holds the configuration for various components of the application.

  Attributes
  ----------
  adr_config : AdrConfig
      Configuration for the ADR (Automated Demand Response) component.
  energy_control_panel_config : Optional[EnergyControlPanelConfig]
      Configuration for the Energy Control Panel component.
  mqtt_config : Optional[MQTTConfig]
      Configuration for the MQTT (Message Queuing Telemetry Transport) component.
  rest_config : RestApiConfig
      Configuration for the REST API component.
  """

  adr_config: AdrConfig
  energy_control_panel_config: Optional[EnergyControlPanelConfig]
  mqtt_config: Optional[MQTTConfig]
  rest_config: RestApiConfig
