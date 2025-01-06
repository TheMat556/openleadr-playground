import logging
import os
import sys
import threading
from datetime import timedelta
from typing import Any, List, Optional

import numpy as np
from dotenv import load_dotenv

from src.mock_node.addons.gradio_ui.async_gradio_app import AsyncGradioApp
from src.node_dashboard.dashboard import GradioNodeDashboard
from src.openadr_node.models import ReportConfiguration
from src.openadr_node.models.mqtt_config import MQTTConfig
from src.openadr_node.models.rest_config import RestApiConfig
from src.openadr_node.node_controller import NodeController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RANDOM_SEED = int(os.getenv('DEV_RANDOM_SEED', 42))
rng = np.random.default_rng(RANDOM_SEED)


def load_environment(env_path: str) -> None:
  """
  Load environment variables from a .env file.

  :param env_path: Path to the .env file.
  :type env_path: str
  """
  load_dotenv(dotenv_path=env_path)


def create_rest_api_config(
  port_env_var: str, default_port: int = 5000
) -> RestApiConfig:
  """
  Create a RestApiConfig instance from environment variables.

  :param port_env_var: Environment variable name for the REST API port.
  :type port_env_var: str
  :param default_port: Default port if the environment variable is not set, defaults to 5000.
  :type default_port: int, optional
  :return: The REST API configuration.
  :rtype: RestApiConfig
  """
  return RestApiConfig(port=int(os.getenv(port_env_var, default_port)))


def create_mqtt_config() -> MQTTConfig:
  """
  Create an MQTTConfig instance from environment variables.

  :return: The MQTT configuration.
  :rtype: MQTTConfig
  """
  return MQTTConfig(
    broker=os.getenv('PRIVATE_MQTT_BROKER_URL'),
    port=int(os.getenv('PRIVATE_MQTT_PORT')),
    topic_load_profile=os.getenv('PRIVATE_MQTT_TOPIC_LOAD_PROFILE'),
    topic_consumption=os.getenv('PRIVATE_MQTT_TOPIC_LOAD_CONSUMPTION'),
    username=os.getenv('PRIVATE_MQTT_USERNAME'),
    password=os.getenv('PRIVATE_MQTT_PASSWORD'),
  )


def run_gradio(interface: Any) -> None:
  """
  Run Gradio in a separate process.

  :param interface: The Gradio interface to launch.
  :type interface: Any
  """
  try:
    interface.launch(
      server_port=int(os.getenv('DEV_GRADIO_PORT', 7860)),
      server_name=os.getenv('DEV_GRADIO_SERVER_NAME', '0.0.0.0'),
    )
  except Exception as e:
    logger.error(f'Error running node dashboard: {e}')


def device_callback() -> float:
  """
  Simulate a device callback.

  :return: Simulated device data.
  :rtype: float
  """
  print('Device callback called')
  return rng.random() * 10


def run_mock_node(queue: Any) -> None:
  """
  Run the mock node.

  :param queue: Queue for inter-process communication.
  :type queue: Any
  """
  load_environment('./development/simple/.env')
  rest_api_config = create_rest_api_config('DEV_MOCK_NODE_REST_API_PORT')

  mock_node = NodeController(
    node_id=os.getenv('DEV_NODE_ID'),
    vtn_name=os.getenv('DEV_VTN_NAME'),
    openadr_vtn_path_prefix=os.getenv('DEV_VTN_PATH_PREFIX'),
    openadr_http_host=os.getenv('DEV_VTN_HTTP_DOMAIN'),
    openadr_http_port=int(os.getenv('DEV_VTN_HTTP_PORT', 80)),
    rest_api_config=rest_api_config,
  )

  def notify_main_process(data: Any) -> None:
    queue.put('vtn_created')

  mock_node.subscribe('vtn_created', notify_main_process)

  app = AsyncGradioApp(slider_file='./slider_values.txt')
  interface = app.create_interface()

  gradio_thread = threading.Thread(target=run_gradio, args=(interface,), daemon=True)
  gradio_thread.start()

  try:
    mock_node.run_node()
  except KeyboardInterrupt:
    sys.exit(0)
  except (ConnectionError, ValueError) as e:
    logger.error(f'Error running mock node: {e}')
    sys.exit(1)
  except Exception as e:
    logger.error(f'Unexpected error running mock node: {e}')
    sys.exit(1)


def run_house_node(
  node_id: str,
  ven_name: str,
  vtn_url: str,
  rest_api_port: str,
  mqtt_broker: Optional[str] = None,
  mqtt_port: Optional[int] = None,
  mqtt_topic_load_profile: Optional[str] = None,
  mqtt_topic_consumption: Optional[str] = None,
  mqtt_username: Optional[str] = None,
  mqtt_password: Optional[str] = None,
) -> None:
  """
  Create and configure a house node.

  :param node_id: The ID of the node.
  :type node_id: str
  :param ven_name: The name of the VEN.
  :type ven_name: str
  :param vtn_url: The URL of the VTN.
  :type vtn_url: str
  :param rest_api_port: The REST API port.
  :type rest_api_port: str
  :param mqtt_broker: The MQTT broker URL, defaults to None.
  :type mqtt_broker: Optional[str], optional
  :param mqtt_port: The MQTT broker port, defaults to None.
  :type mqtt_port: Optional[int], optional
  :param mqtt_topic_load_profile: The MQTT topic for load profile, defaults to None.
  :type mqtt_topic_load_profile: Optional[str], optional
  :param mqtt_topic_consumption: The MQTT topic for consumption, defaults to None.
  :type mqtt_topic_consumption: Optional[str], optional
  :param mqtt_username: The MQTT username, defaults to None.
  :type mqtt_username: Optional[str], optional
  :param mqtt_password: The MQTT password, defaults to None.
  :type mqtt_password: Optional[str], optional
  """
  reports: List[ReportConfiguration] = [
    ReportConfiguration(
      resource_id='res_123',
      measurement='energy',
      sampling_rate=timedelta(seconds=5),
      callback=device_callback,
      additional_metadata={'unit': 'Celsius', 'location': 'Room 101'},
    ),
  ]

  rest_api_config = RestApiConfig(port=int(rest_api_port))

  mqtt_config = MQTTConfig(
    broker=mqtt_broker,
    port=mqtt_port,
    topic_load_profile=mqtt_topic_load_profile,
    topic_consumption=mqtt_topic_consumption,
    username=mqtt_username,
    password=mqtt_password,
  )

  house_node = NodeController(
    node_id=node_id,
    ven_name=ven_name,
    vtn_url=vtn_url,
    rest_api_config=rest_api_config,
    mqtt_config=mqtt_config,
  )
  house_node.add_report(reports)

  try:
    house_node.run_node()
  except KeyboardInterrupt:
    sys.exit(0)
  except (ConnectionError, ValueError) as e:
    logger.error(f'Error running house node: {e}')
    sys.exit(1)
  except Exception as e:
    logger.error(f'Error running house node: {e}')
    sys.exit(1)


def run_node_dashboard() -> None:
  """
  Run the node dashboard.
  """
  dashboard = GradioNodeDashboard(file_path='./development/simple/env_variables.json')
  interface = dashboard.create_interface()
  interface.launch(
    share=False,
    server_port=int(os.getenv('DEV_NODE_DASHBOARD_PORT', 7860)),
    server_name=os.getenv('DEV_GRADIO_SERVER_NAME', '0.0.0.0'),
  )


if __name__ == '__main__':
  run_node_dashboard()
