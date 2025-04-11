import os
import random
import time
from datetime import timedelta
from typing import List

from src.adr_node.config.adr_config import AdrConfig
from src.adr_node.config.mqtt_config import MQTTConfig
from src.adr_node.config.report_config import ReportConfig
from src.adr_node.config.rest_api_config import RestApiConfig
from src.adr_node.config.topic_config import TopicConfig, TopicType
from src.tier_nodes.bottom_node.bottom_node import BottomNode
from src.tier_nodes.bottom_node.config.bottom_node_config import BottomNodeConfig


def temperature_callback() -> float:
  """
  Simulate temperature reading.

  Returns:
      float: Simulated temperature in Celsius
  """
  return 22.5


def energy_callback() -> float:
  """
  Simulate energy consumption reading.

  Returns:
      float: Simulated energy consumption in Watts
  """
  return random.uniform(1, 10)


def create_adr_config() -> AdrConfig:
  """
  Create ADR configuration with environment variables.

  Returns:
      AdrConfig: Configured ADR settings
  """
  return AdrConfig(
    node_id='bottom_001',
    ven_name=os.getenv('OPENADR_VEN_IDENTIFIER', 'ven_001'),
    vtn_url=os.getenv(
      'OPENADR_VTN_CONNECT_URL', 'http://localhost:8080/0/OpenADR2/Simple/2.0b'
    ),
  )


def create_mqtt_config() -> MQTTConfig:
  """
  Create MQTT configuration with topics.

  Returns:
      MQTTConfig: Configured MQTT settings
  """
  mqtt_topics = [
    TopicConfig(topic='load_profile', topic_type=TopicType.PUBLISH),
    TopicConfig(topic='consumption', topic_type=TopicType.SUBSCRIBE),
  ]


  return MQTTConfig(
    broker=os.getenv('MQTT_BROKER_HOST', 'localhost'),
    port=int(os.getenv('MQTT_BROKER_PORT', '1883')),
    username=os.getenv('MQTT_USERNAME', 'mqtt_user'),
    password=os.getenv('MQTT_PASSWORD', 'mqtt_pass'),
    topics=mqtt_topics,
  )


def create_reports() -> List[ReportConfig]:
  """
  Create report configurations for temperature and energy monitoring.

  Returns:
      List[ReportConfig]: List of report configurations
  """
  return [
    ReportConfig(
      resource_id='room_temp_001',
      measurement='temperature',
      sampling_rate=timedelta(seconds=15),
      callback=temperature_callback,
      additional_metadata={'unit': 'celsius', 'location': 'living_room'},
    ),
    ReportConfig(
      resource_id='energy_001',
      measurement='voltage',
      sampling_rate=timedelta(seconds=15),
      callback=energy_callback,
      additional_metadata={'unit': 'watts'},
    ),
  ]


def main() -> None:
  """
  Initialize and run the bottom node with all configurations.
  """
  try:
    # Create configurations
    adr_config = create_adr_config()
    mqtt_config = None
    if os.getenv('MQTT_BROKER_HOST', None) is not None:
      mqtt_config = create_mqtt_config()
    rest_config = RestApiConfig(
      port=int(os.getenv('API_REST_PORT', '5001')),
    )

    # Create bottom node configuration
    bottom_node_config = BottomNodeConfig(
      adr_config=adr_config,
      mqtt_config=mqtt_config if mqtt_config is not None else None,
      rest_config=rest_config,
    )

    # Initialize bottom node
    bottom = BottomNode(bottom_node_config)

    # Add reports
    reports = create_reports()
    bottom.add_reports(reports)

    # Run bottom node
    print('Starting bottom node...')
    bottom.run()

    # Keep the process running
    while True:
      time.sleep(1)

  except KeyboardInterrupt:
    print('\nShutting down bottom node...')
  except Exception as e:
    print(f'Error running bottom node: {e}')
    raise


if __name__ == '__main__':
  main()
