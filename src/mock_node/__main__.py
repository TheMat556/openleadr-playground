import os
import threading

from dotenv import load_dotenv

from src.mock_node.addons.gradio_ui.async_gradio_app import AsyncGradioApp
from src.openadr_node.node_manager import NodeManager


def run_gradio_thread(interface):
  """Run Gradio in a separate thread"""
  try:
    interface.launch(server_port=7862, server_name='0.0.0.0')
  except Exception as e:
    print(f'Failed to launch Gradio interface: {e}')


def main():
  load_dotenv()

  node_manager = NodeManager(
    vtn_name=os.getenv('SERVER_NAME'),
    # ven_name=os.getenv('VEN_NAME'),
    # vtn_url=os.getenv('VTN_URL'),
  )
  app = AsyncGradioApp()
  interface = app.create_interface()
  gradio_thread = threading.Thread(
    target=run_gradio_thread, args=(interface,), daemon=True
  )

  gradio_thread.start()
  node_manager.run_node()


if __name__ == '__main__':
  main()
