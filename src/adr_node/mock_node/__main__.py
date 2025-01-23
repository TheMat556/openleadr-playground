import os
import time

from src.adr_node.config.adr_config import AdrConfig
from src.adr_node.config.rest_api_config import RestApiConfig
from src.adr_node.mock_node_node.config.house_node_config import MockNodeConfig
from src.adr_node.mock_node_node.mock_node import MockNode


def temperature_callback() -> float:
  """Simulate temperature reading"""
  return 22.5


def energy_callback() -> float:
  """Simulate energy consumption reading"""
  return 1250.0


def main():
  adr_config = AdrConfig(
    node_id=os.getenv('NODE_ID', 'mock'),
    vtn_name=os.getenv('VTN_NAME', 'default_vtn'),
    openadr_http_host=os.getenv('VTN_URL', '127.0.0.1'),
    openadr_http_port=int(os.getenv('OPENADR_HTTP_PORT', 8080)),
    openadr_vtn_path_prefix=os.getenv('VTN_PATH_PREFIX', '/0/OpenADR2/Simple/2.0b'),
  )

  rest_config = RestApiConfig(
    port=5000,
  )

  mock_node_config = MockNodeConfig(
    adr_config=adr_config,
    mqtt_config=None,
    rest_config=rest_config,
  )

  mock = MockNode(mock_node_config)

  mock.run()
  while True:
    time.sleep(1)


if __name__ == '__main__':
  main()
