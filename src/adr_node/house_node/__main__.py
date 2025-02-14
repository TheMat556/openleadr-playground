"""
Main entry point for the House OpenADR Node.

This module initializes and runs a house node with temperature and energy
consumption monitoring capabilities.

Created: 2025-02-10 10:27:57
Author: TheMat556
"""

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
from src.adr_node.house_node.config.house_node_config import HouseNodeConfig
from src.adr_node.house_node.house_node import HouseNode


def temperature_callback() -> float:
  """
  Simulate temperature reading.

  Returns:
      float: Simulated temperature in Celsius
  """
  print('Temperature callback')
  return 22.5


def energy_callback() -> float:
  """
  Simulate energy consumption reading.

  Returns:
      float: Simulated energy consumption in Watts
  """
  print('Energy callback')
  return random.uniform(1, 10)


def create_adr_config() -> AdrConfig:
  """
  Create ADR configuration with environment variables.

  Returns:
      AdrConfig: Configured ADR settings
  """
  return AdrConfig(
    node_id='house_001',
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
    TopicConfig(topic='house/load_profile', topic_type=TopicType.PUBLISH),
    TopicConfig(topic='house/consumption', topic_type=TopicType.SUBSCRIBE),
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
      sampling_rate=timedelta(seconds=10),
      callback=temperature_callback,
      additional_metadata={'unit': 'celsius', 'location': 'living_room'},
    ),
    ReportConfig(
      resource_id='energy_001',
      measurement='voltage',
      sampling_rate=timedelta(seconds=10),
      callback=energy_callback,
      additional_metadata={'unit': 'watts'},
    ),
  ]


def main() -> None:
  """
  Initialize and run the house node with all configurations.
  """
  try:
    # Create configurations
    adr_config = create_adr_config()
    mqtt_config = create_mqtt_config()
    rest_config = RestApiConfig(
      port=int(os.getenv('API_REST_PORT', '5001')),
    )

    # Create house node configuration
    house_node_config = HouseNodeConfig(
      adr_config=adr_config,
      mqtt_config=mqtt_config,
      rest_config=rest_config,
    )

    # Initialize house node
    house = HouseNode(house_node_config)

    # Add reports
    reports = create_reports()
    house.add_reports(reports)

    # Run house node
    print('Starting house node...')
    house.run()

    # Keep the process running
    while True:
      time.sleep(1)

  except KeyboardInterrupt:
    print('\nShutting down house node...')
  except Exception as e:
    print(f'Error running house node: {e}')
    raise


if __name__ == '__main__':
  main()
