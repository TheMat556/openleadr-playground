import os
import sys
import threading
from datetime import timedelta

import numpy as np
from dotenv import load_dotenv

from src.mock_node.addons.gradio_ui.async_gradio_app import AsyncGradioApp
from src.node_dashboard.dashboard import GradioNodeDashboard
from src.openadr_node.models import ReportConfiguration
from src.openadr_node.node_manager import NodeManager


def run_mock_node(queue):
  load_dotenv(dotenv_path='./development_configs/simple/.env')

  mock_node = NodeManager(
    vtn_name=os.getenv('DEV_VTN_NAME'),
    vtn_path_prefix=os.getenv('DEV_VTN_PATH_PREFIX'),
    rest_api_port=os.getenv('DEV_MOCK_NODE_REST_API'),
    http_host=os.getenv('DEV_VTN_HTTP_DOMAIN'),
    http_port=os.getenv('DEV_VTN_HTTP_PORT'),
  )

  def notify_main_process(data):
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


def run_gradio(interface):
  """Run Gradio in a separate process."""
  try:
    interface.launch(
      server_port=int(os.getenv('DEV_GRADIO_PORT')),
      server_name=os.getenv('DEV_GRADIO_SERVER_NAME'),
    )
  except Exception as e:
    print(f'Failed to launch Gradio interface: {e}')


def device_callback():
  """Simulate a device callback."""
  print('Device callback called')
  return np.random.rand() * 10


def run_house_node(ven_name: str, vtn_url: str, rest_api_port: str):
  """Create and configure a house node."""
  reports = [
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
    rest_api_port=rest_api_port,
  )
  house_node.add_report(reports)

  try:
    house_node.run_node()
  except KeyboardInterrupt:
    sys.exit(0)


def run_node_dashboard():
  """Run the node dashboard."""
  gradio_node_dashboard = GradioNodeDashboard(
    file_path='./development_configs/simple/env_variables.json'
  )
  interface = gradio_node_dashboard.create_interface()
  interface.launch(
    share=False,
    server_port=int(os.getenv('DEV_NODE_DASHBOARD_PORT')),
    server_name=os.getenv('DEV_GRADIO_SERVER_NAME'),
  )
