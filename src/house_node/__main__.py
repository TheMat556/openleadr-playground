import logging
import os
import sys
from datetime import timedelta
from typing import List

import numpy as np
from dotenv import load_dotenv

from src.openadr_node.models import ReportConfiguration
from src.openadr_node.models.mqtt_config import MQTTConfig
from src.openadr_node.models.rest_config import RestApiConfig
from src.openadr_node.node_controller import NodeController

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


seed = 42
rng = np.random.default_rng(seed)


def sample_callback_1() -> float:
  print('callback 1')
  return rng.random() * 10


def sample_callback_2() -> float:
  print('callback 2')
  return rng.random() * 10


def main() -> None:
  load_dotenv()
  reports: List[ReportConfiguration] = [
    ReportConfiguration(
      resource_id='res_123',
      measurement='energy',
      sampling_rate=timedelta(seconds=5),
      callback=sample_callback_1,
      additional_metadata={'unit': 'Celsius', 'location': 'Room 101'},
    ),
    ReportConfiguration(
      resource_id='res_456',
      measurement='energy',
      sampling_rate=timedelta(seconds=5),
      callback=sample_callback_2,
      additional_metadata={'unit': '%', 'location': 'Room 202'},
    ),
  ]

  mqtt_config = None

  if os.getenv('PRIVATE_MQTT_BROKER_URL', None):
    mqtt_config = MQTTConfig(
      broker=os.getenv('PRIVATE_MQTT_BROKER_URL'),
      port=int(os.getenv('PRIVATE_MQTT_PORT')),
      topic_load_profile=os.getenv('PRIVATE_MQTT_TOPIC_LOAD_PROFILE'),
      topic_consumption=os.getenv('PRIVATE_MQTT_TOPIC_LOAD_CONSUMPTION'),
      username=os.getenv('PRIVATE_MQTT_USERNAME'),
      password=os.getenv('PRIVATE_MQTT_PASSWORD'),
    )

  rest_api_config = RestApiConfig(port=int(os.getenv('REST_API_PORT', 5000)))

  node_manager = NodeController(
    node_id=os.getenv('NODE_ID'),
    ven_name=os.getenv('VEN_NAME'),
    vtn_url=os.getenv('CONNECT_VTN_URL'),
    mqtt_config=mqtt_config,
    rest_api_config=rest_api_config,
  )

  node_manager.add_report(reports)
  try:
    node_manager.run_node()
  except KeyboardInterrupt:
    sys.exit(0)
  except Exception as e:
    logger.error(f'Error running node: {e}')
    sys.exit(1)


if __name__ == '__main__':
  main()
