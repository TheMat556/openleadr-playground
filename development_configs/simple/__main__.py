import os
import sys
import threading
import asyncio
from datetime import timedelta

import numpy as np
from dotenv import load_dotenv

from src.mock_node.addons.gradio_ui.async_gradio_app import AsyncGradioApp
from src.openadr_node.models import ReportConfiguration
from src.openadr_node.node_manager import NodeManager

# Create a thread-local data object
thread_local = threading.local()


def run_gradio_thread(interface):
  """Run Gradio in a separate thread."""
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


def create_house_node():
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
    ven_name=os.getenv('DEV_VEN_NAME'),
    vtn_url=os.getenv('DEV_VTN_URL'),
    rest_api_port=os.getenv('DEV_HOUSE_NODE_REST_API'),
  )
  house_node.add_report(reports)
  return house_node


def on_mock_node_creation():
  """Handle mock node creation."""
  house_node = create_house_node()
  house_node.run_node()


def thread_main():
  """Main function to initialize and run the application in a thread."""
  load_dotenv(dotenv_path='./development_configs/simple/.env')
  print(os.getenv('DEV_VTN_NAME'))

  # Create a new event loop for this thread
  asyncio.set_event_loop(asyncio.new_event_loop())

  mock_node = NodeManager(
    vtn_name=os.getenv('DEV_VTN_NAME'),
    vtn_path_prefix=os.getenv('DEV_VTN_PATH_PREFIX'),
    rest_api_port=os.getenv('DEV_MOCK_NODE_REST_API'),
    http_host=os.getenv('DEV_VTN_HTTP_DOMAIN'),
    http_port=os.getenv('DEV_VTN_HTTP_PORT'),
  )
  mock_node.subscribe_to_node_creation(on_mock_node_creation)

  app = AsyncGradioApp(slider_file='./slider_values.txt')
  interface = app.create_interface()

  gradio_thread = threading.Thread(
    target=run_gradio_thread, args=(interface,), daemon=True
  )
  gradio_thread.start()

  # Uncomment if needed
  # gradio_node_dashboard = GradioNodeDashboard()
  # dashboard_interface = gradio_node_dashboard.create_interface()
  # dashboard_thread = threading.Thread(
  #     target=dashboard_interface.launch,
  #     kwargs={
  #         'share': False,
  #         'server_port': int(os.getenv('DEV_NODE_DASHBOARD_PORT')),
  #         'server_name': '127.0.0.1',
  #     },
  #     daemon=True
  # )
  # dashboard_thread.start()

  try:
    mock_thread = threading.Thread(target=mock_node.run_node(), daemon=True)
    mock_thread.start()
  except KeyboardInterrupt:
    sys.exit(0)


def main():
  """Main entry point for the application."""
  # Each thread will have its own context
  thread = threading.Thread(target=thread_main)
  thread.start()
  thread.join()


if __name__ == '__main__':
  main()
