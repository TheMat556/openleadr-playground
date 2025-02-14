import os
import time
from typing import Optional, Any

from src.adr_node.config.adr_config import AdrConfig
from src.adr_node.config.rest_api_config import RestApiConfig
from src.adr_node.mock_node_dashboard.config.app_config import EnergyControlPanelConfig
from src.adr_node.top_node.config.top_node_config import TopNodeConfig
from src.adr_node.top_node.top_node import TopNode


def temperature_callback() -> float:
  """
  Simulate temperature reading.

  Returns:
      float: Simulated temperature value in Celsius
  """
  return 22.5


def energy_callback() -> float:
  """
  Simulate energy consumption reading.

  Returns:
      float: Simulated energy consumption in kWh
  """
  return 1250.0


def get_env_value(
  key: str, default: Optional[str] = None, convert: callable = str
) -> Any:
  """
  Get environment variable with type conversion and default value.

  Args:
      key: Environment variable key
      default: Default value if key not found
      convert: Function to convert the value

  Returns:
      Converted environment variable value
  """
  value = os.getenv(key, default)
  try:
    return convert(value) if value is not None else None
  except (ValueError, TypeError) as e:
    raise ValueError(f'Error converting environment variable {key}: {e}')


def main() -> None:
  """
  Initialize and run the mock OpenADR node.
  """
  # ADR Configuration
  adr_config = AdrConfig(
    node_id=get_env_value('OPENADR_NODE_ID', 'mock'),
    vtn_name=get_env_value('OPENADR_VTN_IDENTIFIER', 'default_vtn'),
    openadr_http_host=get_env_value('OPENADR_VTN_HOST', '0.0.0.0'),
    openadr_http_port=get_env_value('OPENADR_VTN_PORT', '8080', int),
    openadr_vtn_path_prefix=get_env_value(
      'OPENADR_VTN_PATH_PREFIX', '/0/OpenADR2/Simple/2.0b'
    ),
  )

  # REST API Configuration
  rest_config = RestApiConfig(
    port=get_env_value('API_REST_PORT', '5010', int),
  )

  # Energy Control Panel Configuration
  energy_control_panel_config = EnergyControlPanelConfig(
    slider_file_path='./development/simple/data/sliders.json',
  )

  # Mock Node Configuration
  mock_node_config = TopNodeConfig(
    energy_control_panel_config=energy_control_panel_config,
    adr_config=adr_config,
    mqtt_config=None,
    rest_config=rest_config,
  )

  try:
    print(energy_control_panel_config)
    print(adr_config)
    print(rest_config)
    print(mock_node_config)
    # Initialize and run mock node
    mock = TopNode(mock_node_config)
    mock.run()

    # Keep the process running
    while True:
      time.sleep(1)
  except KeyboardInterrupt:
    print('\nShutting down mock node...')
  except Exception as e:
    print(f'Error running mock node: {e}')
    raise


def run_mock_node(mock_node_config: TopNodeConfig):
  mock_node = TopNode(mock_node_config)
  mock_node.run()
  while True:
    time.sleep(1)


if __name__ == '__main__':
  main()
