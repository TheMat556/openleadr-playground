import asyncio
import logging
import os
import random
from datetime import timedelta
from typing import List

from dotenv import load_dotenv

from src.house_node.house_node import HouseNode
from src.house_node.config import HouseNodeConfig
from src.mock_node.mock_node import MockNode
from src.mock_node.config import MockNodeConfig
from src.node_dashboard.dashboard import GradioNodeDashboard
from src.openadr_node.models import ReportConfiguration
from src.openadr_node.models.mqtt_config import MQTTConfig
from src.openadr_node.models.topic_config import TopicConfig, TopicType

logging.basicConfig(
  level=os.getenv('LOG_LEVEL', 'INFO'),
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def device_callback() -> float:
  """Simulate a device callback."""
  print('Device callback called')
  return random.random() * 10


def create_report_configurations() -> List[ReportConfiguration]:
  reports: List[ReportConfiguration] = [
    ReportConfiguration(
      resource_id=f'res_{random.randint(100, 999)}',
      measurement='energy',
      sampling_rate=timedelta(seconds=10),
      callback=device_callback,
      additional_metadata={'unit': 'Celsius', 'location': 'Room 101'},
    ),
  ]
  return reports


async def run_dashboard():
  """Run node dashboard asynchronously"""
  dashboard = GradioNodeDashboard(file_path='./development/simple/env_variables.json')
  interface = dashboard.create_interface()
  interface.launch(
    show_api=False,
    share=False,
    server_port=int(os.getenv('DEV_NODE_DASHBOARD_PORT', 7860)),
    server_name=os.getenv('DEV_GRADIO_SERVER_NAME', '0.0.0.0'),
  )


async def main():
  # Load environment variables
  load_dotenv(dotenv_path='./development/simple/.env')
  load_dotenv(dotenv_path='./development/simple/.env.mqtt')

  # Setup mock node
  mock_config = MockNodeConfig(
    node_id=os.getenv('DEV_NODE_ID'),
    vtn_name=os.getenv('VTN_NAME', 'default_vtn'),
    openadr_http_host=os.getenv('VTN_URL', '127.0.0.1'),
    openadr_http_port=int(os.getenv('OPENADR_HTTP_PORT', 8080)),
    openadr_vtn_path_prefix=os.getenv('VTN_PATH_PREFIX', '/0/OpenADR2/Simple/2.0b'),
    rest_api_port=int(os.getenv('REST_API_PORT', 5000)),
    gradio_port=int(os.getenv('GRADIO_PORT', 7860)),
    gradio_host=os.getenv('GRADIO_SERVER_NAME', '0.0.0.0'),
  )
  mock_node = MockNode(mock_config)

  # Setup house nodes
  house_node_0_config = HouseNodeConfig(
    node_id=os.getenv('DEV_NODE_ID_0_0'),
    ven_name=os.getenv('DEV_VEN_NAME_0'),
    vtn_url=os.getenv('DEV_VTN_URL'),
    rest_api_port=int(os.getenv('DEV_HOUSE_NODE_0_REST_API', '5001')),
  )

  # Add MQTT config if needed
  if os.getenv('PRIVATE_MQTT_BROKER_URL'):
    mqtt_topics = [
      TopicConfig(
        topic=os.getenv('PRIVATE_MQTT_TOPIC_LOAD_PROFILE'), topic_type=TopicType.PUBLISH
      ),
      TopicConfig(
        topic=os.getenv('PRIVATE_MQTT_TOPIC_LOAD_CONSUMPTION'),
        topic_type=TopicType.SUBSCRIBE,
      ),
    ]
    house_node_0_config.mqtt_config = MQTTConfig(
      broker=os.getenv('PRIVATE_MQTT_BROKER_URL'),
      port=int(os.getenv('PRIVATE_MQTT_PORT', 0)),
      username=os.getenv('PRIVATE_MQTT_USERNAME'),
      password=os.getenv('PRIVATE_MQTT_PASSWORD'),
      client_id=os.getenv('DEV_NODE_ID_0_0'),
      topics=mqtt_topics,
    )

  house_node_0 = HouseNode(house_node_0_config)
  house_node_0.add_reports(create_report_configurations())

  house_node_1 = HouseNode(
    HouseNodeConfig(
      node_id=os.getenv('DEV_NODE_ID_0_1'),
      ven_name=os.getenv('DEV_VEN_NAME_1'),
      vtn_url=os.getenv('DEV_VTN_URL'),
      rest_api_port=int(os.getenv('DEV_HOUSE_NODE_1_REST_API')),
    )
  )
  house_node_1.add_reports(create_report_configurations())

  # Start each task individually
  tasks = []
  tasks.append(asyncio.create_task(mock_node.run()))
  await asyncio.sleep(10)

  print('Starting house nodes 0')
  tasks.append(asyncio.create_task(house_node_0.run()))
  await asyncio.sleep(10)

  print('Starting house nodes 1')
  tasks.append(asyncio.create_task(house_node_1.run()))
  await asyncio.sleep(10)

  tasks.append(asyncio.create_task(run_dashboard()))

  try:
    # Wait for all tasks to complete
    await asyncio.gather(*tasks)
  except Exception as e:
    logger.error(f'Error running nodes: {e}')
    for task in tasks:
      task.cancel()
    raise


if __name__ == '__main__':
  asyncio.run(main())
