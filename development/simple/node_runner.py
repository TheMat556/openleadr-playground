import logging
import os
import sys
import threading
from datetime import timedelta
from typing import Any, List

import numpy as np
from dotenv import load_dotenv

from src.mock_node.addons.gradio_ui.async_gradio_app import AsyncGradioApp
from src.node_dashboard.dashboard import GradioNodeDashboard
from src.openadr_node.models import ReportConfiguration
from src.openadr_node.node_manager import NodeManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_mock_node(queue: Any) -> None:
  load_dotenv(dotenv_path='./development/simple/.env')

  mock_node = NodeManager(
    vtn_name=os.getenv('DEV_VTN_NAME'),
    vtn_path_prefix=os.getenv('DEV_VTN_PATH_PREFIX'),
    rest_api_port=int(os.getenv('DEV_MOCK_NODE_REST_API_PORT', 5000)),
    http_host=os.getenv('DEV_VTN_HTTP_DOMAIN'),
    http_port=int(os.getenv('DEV_VTN_HTTP_PORT', 80)),
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
    logging.error(f'Error running mock node: {e}')
    sys.exit(1)
  except Exception as e:
    logger.error(f'Unexpected error running mock node: {e}')
    sys.exit(1)


def run_gradio(interface: Any) -> None:
  """Run Gradio in a separate process."""
  try:
    interface.launch(
      server_port=int(os.getenv('DEV_GRADIO_PORT', 7860)),
      server_name=os.getenv('DEV_GRADIO_SERVER_NAME', '0.0.0.0'),
    )
  except Exception as e:
    logger.error(f'Error running node dashboard: {e}')


rng = np.random.default_rng()


def device_callback() -> float:
  """Simulate a device callback."""
  print('Device callback called')
  return rng.random() * 10


def run_house_node(ven_name: str, vtn_url: str, rest_api_port: str) -> None:
  """Create and configure a house node."""
  reports: List[ReportConfiguration] = [
    ReportConfiguration(
      resource_id='res_123',
      measurement='energy',
      sampling_rate=timedelta(seconds=5),
      callback=device_callback,
      additional_metadata={'unit': 'Celsius', 'location': 'Room 101'},
    ),
  ]
  house_node = NodeManager(
    ven_name=ven_name,
    vtn_url=vtn_url,
    rest_api_port=int(rest_api_port),
  )
  house_node.add_report(reports)

  try:
    house_node.run_node()
  except KeyboardInterrupt:
    sys.exit(0)
  except (ConnectionError, ValueError) as e:
    logging.error(f'Error running mock node: {e}')
    sys.exit(1)
  except Exception as e:
    logger.error(f'Error running house node: {e}')
    sys.exit(1)


def run_node_dashboard() -> None:
  """Run the node dashboard."""
  gradio_node_dashboard = GradioNodeDashboard(
    file_path='./development/simple/env_variables.json'
  )
  interface = gradio_node_dashboard.create_interface()
  interface.launch(
    share=False,
    server_port=int(os.getenv('DEV_NODE_DASHBOARD_PORT', 7860)),
    server_name=os.getenv('DEV_GRADIO_SERVER_NAME', '0.0.0.0'),
  )
