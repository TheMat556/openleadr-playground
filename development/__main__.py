import logging
import os
import random
import threading
import time
from datetime import timedelta
from typing import List

from dotenv import load_dotenv

from src.adr_node.config.adr_config import AdrConfig
from src.adr_node.config.report_config import ReportConfig
from src.adr_node.config.rest_api_config import RestApiConfig
from src.adr_node.house_node.config.house_node_config import HouseNodeConfig
from src.adr_node.house_node.house_node import HouseNode
from src.adr_node.mock_node_dashboard.config.app_config import EnergyControlPanelConfig
from src.adr_node.top_node.config.top_node_config import TopNodeConfig
from src.adr_node.top_node.top_node import TopNode
from src.node_dashboard.dashboard import GradioNodeDashboard

logging.basicConfig(
  level=os.getenv('LOG_LEVEL', 'INFO'),
  format='%(asctime)s - %(name)s - %(levelname=s - %(message)s',
)
logger = logging.getLogger(__name__)


def device_callback() -> float:
  """Simulate a device callback."""
  print('Device callback called')
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


def run_house_node(house_node_config: HouseNodeConfig):
  house_node = HouseNode(house_node_config)
  house_node.add_reports(create_report_configurations())
  house_node.run()
  while True:
    time.sleep(1)


def run_mock_node(mock_node_config: TopNodeConfig):
  mock_node = TopNode(mock_node_config)
  mock_node.run()
  while True:
    time.sleep(1)


def run_network_dashboard():
  """Run node dashboard asynchronously"""
  dashboard = GradioNodeDashboard(file_path='./development/env/env_variables.json')
  interface = dashboard.create_interface()
  # interface.queue()
  interface.launch(
    server_port=7860,
    server_name='127.0.0.1',
  )


def main():
  # Load environment variables
  load_dotenv(dotenv_path='./development/simple/.env')
  load_dotenv(dotenv_path='./development/simple/.env.mqtt')

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
    ven_name=os.getenv('VEN_NAME', 'default_ven'),
    vtn_url=os.getenv('DEV_VTN_URL', 'http://127.0.0.1:8080/0/OpenADR2/Simple/2.0b'),
  )

  house_rest_config = RestApiConfig(
    port=5001,
  )

  house_node_config = HouseNodeConfig(
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

  house2_node_config = HouseNodeConfig(
    adr_config=house2_adr_config,
    mqtt_config=None,
    rest_config=house2_rest_config,
  )

  # Create and start the threads for house nodes and mock node
  house_node_thread = threading.Thread(target=run_house_node, args=(house_node_config,))
  house2_node_thread = threading.Thread(
    target=run_house_node, args=(house2_node_config,)
  )
  mock_node_thread = threading.Thread(target=run_mock_node, args=(mock_node_config,))

  mock_node_thread.start()
  time.sleep(1)
  house_node_thread.start()
  time.sleep(1)
  house2_node_thread.start()

  run_network_dashboard()


if __name__ == '__main__':
  main()
