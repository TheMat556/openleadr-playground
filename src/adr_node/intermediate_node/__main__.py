import os
import time
from typing import Optional, Any

from src.adr_node.config.adr_config import AdrConfig
from src.adr_node.config.rest_api_config import RestApiConfig
from src.adr_node.config.mqtt_config import MQTTConfig
from src.adr_node.intermediate_node.config.intermediate_node_config import (
  IntermediateNodeConfig,
)
from src.adr_node.intermediate_node.intermediate_node import IntermediateNode


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


def validate_config() -> None:
  required_vars = [
    'OPENADR_NODE_ID',
    'OPENADR_VTN_IDENTIFIER',
    'OPENADR_VTN_CONNECT_URL',
    'OPENADR_VTN_PORT',
    'OPENADR_VTN_HOST',
    'VEN_NAME',
    'CONNECT_VTN_URL',
  ]
  missing_vars = [var for var in required_vars if not os.getenv(var)]
  print('MISSING VARS', missing_vars)
  if missing_vars:
    raise ValueError(
      f'Missing required environment variables: {", ".join(missing_vars)}'
    )


def main() -> None:
  """
  Initialize and run the intermediate OpenADR node.
  """
  # validate_config()

  # ADR Configuration
  adr_config = AdrConfig(
    node_id=get_env_value('OPENADR_NODE_ID', 'intermediate'),
    vtn_name=get_env_value('OPENADR_VTN_IDENTIFIER', 'default_vtn'),
    openadr_http_host=get_env_value('OPENADR_VTN_HOST', '0.0.0.0'),
    openadr_http_port=get_env_value('OPENADR_VTN_PORT', '8080', int),
    openadr_vtn_path_prefix=get_env_value('OPENADR_VTN_PATH_PREFIX'),
    ven_name=get_env_value('OPENADR_VEN_IDENTIFIER', 'default_ven'),
    vtn_url=get_env_value(
      'OPENADR_VTN_CONNECT_URL', 'http://localhost:8084/0/1/OpenADR2/Simple/2.0b'
    ),
  )
  print('ADR CONFIG', adr_config)

  # REST API Configuration
  rest_config = RestApiConfig(
    port=get_env_value('API_REST_PORT', '5000', int),
  )

  # MQTT Configuration (Optional)
  mqtt_config = None
  if get_env_value('MQTT_ENABLED', 'false').lower() == 'true':
    mqtt_config = MQTTConfig(
      broker=get_env_value('MQTT_BROKER', 'localhost'),
      port=get_env_value('MQTT_PORT', '1883', int),
      topic=get_env_value('MQTT_TOPIC', 'openadr/events'),
    )

  # Intermediate Node Configuration
  intermediate_node_config = IntermediateNodeConfig(
    adr_config=adr_config,
    mqtt_config=mqtt_config,
    rest_config=rest_config,
    ven_name=get_env_value('VEN_NAME'),
    vtn_url=get_env_value('CONNECT_VTN_URL'),
  )

  try:
    print('Configuration loaded:')
    print(f'ADR Config: {adr_config}')
    print(f'REST Config: {rest_config}')
    print(f'MQTT Config: {mqtt_config}')

    # Initialize and run intermediate node
    node = IntermediateNode(intermediate_node_config)
    node.run()

    # Keep the process running
    while True:
      time.sleep(1)
  except KeyboardInterrupt:
    print('\nShutting down intermediate node...')
  except Exception as e:
    print(f'Error running intermediate node: {e}')
    raise


def run_intermediate_node(config: IntermediateNodeConfig):
  node = IntermediateNode(config)
  node.run()
  while True:
    time.sleep(1)


if __name__ == '__main__':
  main()
