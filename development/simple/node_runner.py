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
from src.openadr_node.node_manager import NodeManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

seed = 42
rng = np.random.default_rng(seed)


def load_environment(env_path: str) -> None:
  """Load environment variables from a .env file.

  Parameters
  ----------
  env_path : str
      Path to the .env file.
  """
  load_dotenv(dotenv_path=env_path)


def create_rest_api_config(
  port_env_var: str, default_port: int = 5000
) -> RestApiConfig:
  """Create a RestApiConfig instance from environment variables.

  Parameters
  ----------
  port_env_var : str
      Environment variable name for the REST API port.
  default_port : int, optional
      Default port if the environment variable is not set, by default 5000.

  Returns
  -------
  RestApiConfig
      The REST API configuration.
  """
  return RestApiConfig(port=int(os.getenv(port_env_var, default_port)))


def create_mqtt_config() -> MQTTConfig:
  """Create an MQTTConfig instance from environment variables.

  Returns
  -------
  MQTTConfig
      The MQTT configuration.
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
  """Run Gradio in a separate process.

  Parameters
  ----------
  interface : Any
      The Gradio interface to launch.
  """
  try:
    interface.launch(
      server_port=int(os.getenv('DEV_GRADIO_PORT', 7860)),
      server_name=os.getenv('DEV_GRADIO_SERVER_NAME', '0.0.0.0'),
    )
  except Exception as e:
    logger.error(f'Error running node dashboard: {e}')


def device_callback() -> float:
  """Simulate a device callback.

  Returns
  -------
  float
      Simulated device data.
  """
  print('Device callback called')
  return rng.random() * 10


def run_mock_node(queue: Any) -> None:
  """Run the mock node.

  Parameters
  ----------
  queue : Any
      Queue for inter-process communication.
  """
  load_environment('./development/simple/.env')
  rest_api_config = create_rest_api_config('DEV_MOCK_NODE_REST_API_PORT')

  mock_node = NodeManager(
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
  """Create and configure a house node.

  Parameters
  ----------
  node_id : str
      The ID of the node.
  ven_name : str
      The name of the VEN.
  vtn_url : str
      The URL of the VTN.
  rest_api_port : str
      The REST API port.
  mqtt_broker : Optional[str], optional
      The MQTT broker URL, by default None.
  mqtt_port : Optional[int], optional
      The MQTT broker port, by default None.
  mqtt_topic_load_profile : Optional[str], optional
      The MQTT topic for load profile, by default None.
  mqtt_topic_consumption : Optional[str], optional
      The MQTT topic for consumption, by default None.
  mqtt_username : Optional[str], optional
      The MQTT username, by default None.
  mqtt_password : Optional[str], optional
      The MQTT password, by default None.
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

  house_node = NodeManager(
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
  """Run the node dashboard."""
  dashboard = GradioNodeDashboard(file_path='./development/simple/env_variables.json')
  interface = dashboard.create_interface()
  interface.launch(
    share=False,
    server_port=int(os.getenv('DEV_NODE_DASHBOARD_PORT', 7860)),
    server_name=os.getenv('DEV_GRADIO_SERVER_NAME', '0.0.0.0'),
  )


# Example of how to use the functions
if __name__ == '__main__':
  run_node_dashboard()
