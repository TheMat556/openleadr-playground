import logging
import os
import random
import threading
import time
from datetime import timedelta
from typing import List

from dotenv import load_dotenv

from src.adr_node.config.adr_config import AdrConfig
from src.adr_node.config.mqtt_config import MQTTConfig
from src.adr_node.config.report_config import ReportConfig
from src.adr_node.config.rest_api_config import RestApiConfig
from src.adr_node.config.topic_config import TopicConfig, TopicType
from src.adr_node.mock_node_dashboard.config.app_config import EnergyControlPanelConfig
from src.network_dashboard.dashboard import NetworkDashboard
from src.tier_nodes.bottom_node.bottom_node import BottomNode
from src.tier_nodes.bottom_node.config.bottom_node_config import BottomNodeConfig
from src.tier_nodes.top_node.config.top_node_config import TopNodeConfig
from src.tier_nodes.top_node.top_node import TopNode

logging.basicConfig(
  level=os.getenv('LOG_LEVEL', 'INFO'),
  format='%(asctime)s - %(name)s - %(levelname=s - %(message)s',
)
logger = logging.getLogger(__name__)


def device_callback() -> float:
  """Simulate a device callback."""
  return random.random() * 10


def create_report_configurations() -> List[ReportConfig]:
  reports: List[ReportConfig] = [
    ReportConfig(
      resource_id=f'res_{random.randint(100, 999)}',
      measurement='celcius',
      sampling_rate=timedelta(seconds=10),
      callback=device_callback,
      additional_metadata={'unit': 'Celsius', 'location': 'Room 101'},
    ),
    ReportConfig(
      resource_id=f'res_{random.randint(100, 999)}',
      measurement='energy',
      sampling_rate=timedelta(seconds=10),
      callback=device_callback,
    ),
  ]
  return reports


def run_bottom_node(bottom_node_config: BottomNodeConfig):
  bottom_node = BottomNode(bottom_node_config)
  bottom_node.add_reports(create_report_configurations())
  bottom_node.run()
  while True:
    time.sleep(1)


def run_mock_node(mock_node_config: TopNodeConfig):
  mock_node = TopNode(mock_node_config)
  mock_node.run()
  while True:
    time.sleep(1)


def run_network_dashboard():
  """Run node dashboard asynchronously"""
  dashboard = NetworkDashboard(file_path='./development/env/env_variables.json')
  interface = dashboard.create_interface()
  # interface.queue()
  interface.launch(
    server_port=7860,
    server_name='127.0.0.1',
  )


def main():
  # Load environment variables
  load_dotenv(dotenv_path='./development/env/.env')
  load_dotenv(dotenv_path='./development/env/.env.mqtt')

  # Setup mock node
  mock_adr_config = AdrConfig(
    node_id=os.getenv('NODE_ID', 'mock'),
    vtn_name=os.getenv('VTN_NAME', 'default_vtn'),
    openadr_http_host=os.getenv('VTN_URL', '0.0.0.0'),
    openadr_http_port=int(os.getenv('OPENADR_HTTP_PORT', 8080)),
    openadr_vtn_path_prefix=os.getenv('VTN_PATH_PREFIX', '/0/OpenADR2/Simple/2.0b'),
  )

  mock_rest_config = RestApiConfig(
    port=5000,
  )

  energy_control_panel_config = EnergyControlPanelConfig(
    slider_file_path='./development/simple/data/sliders.json',
  )

  mock_node_config = TopNodeConfig(
    energy_control_panel_config=energy_control_panel_config,
    adr_config=mock_adr_config,
    mqtt_config=None,
    rest_config=mock_rest_config,
  )

  house_adr_config = AdrConfig(
    node_id=os.getenv('NODE_ID', 'house'),
    ven_name=os.getenv('VEN_NAME', 'default_ven1'),
    vtn_url=os.getenv('DEV_VTN_URL', 'http://127.0.0.1:8080/0/OpenADR2/Simple/2.0b'),
  )

  house_rest_config = RestApiConfig(
    port=5001,
  )

  bottom_node_config = BottomNodeConfig(
    adr_config=house_adr_config,
    mqtt_config=None,
    rest_config=house_rest_config,
  )

  house2_adr_config = AdrConfig(
    node_id='house2',
    ven_name='default_ven2',
    vtn_url='http://127.0.0.1:8080/0/OpenADR2/Simple/2.0b',
  )

  house2_rest_config = RestApiConfig(
    port=5002,
  )

  house_2_mqtt_config = MQTTConfig(
    broker=os.getenv('MQTT_BROKER_URL', None),
    port=int(os.getenv('MQTT_PORT', None)),
    username=os.getenv('MQTT_USERNAME', None),
    password=os.getenv('MQTT_PASSWORD', None),
    topics=[
      TopicConfig(
        topic='load-profile',
        topic_type=TopicType.PUBLISH,
      ),
      TopicConfig(
        topic='consumption',
        topic_type=TopicType.SUBSCRIBE,
      ),
    ],
  )

  house2_node_config = BottomNodeConfig(
    adr_config=house2_adr_config,
    mqtt_config=house_2_mqtt_config,
    rest_config=house2_rest_config,
  )

  # Create and start the threads for house nodes and mock node
  bottom_node_thread = threading.Thread(
    target=run_bottom_node, args=(bottom_node_config,)
  )
  house2_node_thread = threading.Thread(
    target=run_bottom_node, args=(house2_node_config,)
  )
  mock_node_thread = threading.Thread(target=run_mock_node, args=(mock_node_config,))

  mock_node_thread.start()
  time.sleep(1)
  bottom_node_thread.start()
  time.sleep(1)
  house2_node_thread.start()

  run_network_dashboard()


if __name__ == '__main__':
  main()
