import asyncio
import logging
from datetime import timedelta

from src.house_node.config import HouseNodeConfig
from src.openadr_node.models import ReportConfiguration
from src.openadr_node.protocols.mqtt.config.mqtt_config import MQTTConfig
from src.openadr_node.models.topic_config import TopicConfig, TopicType
from src.house_node.house_node import HouseNode

# Configure logging
logging.basicConfig(
  level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def temperature_callback() -> float:
  """Simulate temperature reading"""
  return 22.5


def energy_callback() -> float:
  """Simulate energy consumption reading"""
  return 1250.0


async def main():
  # Basic configuration
  config = HouseNodeConfig(
    node_id='house_001',
    ven_name='ven_001',
    vtn_url='http://localhost:8080/0/OpenADR2/Simple/2.0b',
    rest_api_port=5000,
  )

  # Optional: Add MQTT configuration
  mqtt_topics = [
    TopicConfig(topic='house/load_profile', topic_type=TopicType.PUBLISH),
    TopicConfig(topic='house/consumption', topic_type=TopicType.SUBSCRIBE),
  ]

  config.mqtt_config = MQTTConfig(
    broker='localhost',
    port=1883,
    username='mqtt_user',
    password='mqtt_pass',
    client_id='house_001',
    topics=mqtt_topics,
  )

  # Create house node
  house = HouseNode(config)

  # Add reports
  reports = [
    ReportConfiguration(
      resource_id='room_temp_001',
      measurement='temperature',
      sampling_rate=timedelta(seconds=60),
      callback=temperature_callback,
      additional_metadata={'unit': 'celsius', 'location': 'living_room'},
    ),
    ReportConfiguration(
      resource_id='energy_001',
      measurement='power',
      sampling_rate=timedelta(seconds=300),
      callback=energy_callback,
      additional_metadata={'unit': 'watts'},
    ),
  ]

  house.add_reports(reports)

  try:
    await house.run()
  except KeyboardInterrupt:
    logger.info('Shutting down house node...')
  except Exception as e:
    logger.error(f'Error running house node: {e}')
    raise


if __name__ == '__main__':
  asyncio.run(main())
