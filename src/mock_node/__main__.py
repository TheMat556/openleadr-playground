import os
import threading

from dotenv import load_dotenv

from src.mock_node.addons.gradio_ui.async_gradio_app import AsyncGradioApp
from src.openadr_node.node_manager import NodeManager


def run_gradio_thread(interface: AsyncGradioApp) -> None:
  """Run Gradio in a separate thread"""
  try:
    interface.launch(
      server_port=int(os.getenv('GRADIO_PORT', 7860)),
      server_name=os.getenv('GRADIO_SERVER_NAME', '0.0.0.0'),
    )
  except Exception as e:
    print(f'Failed to launch Gradio interface: {e}')


def main() -> None:
  def cleanup() -> None:
    if gradio_thread.is_alive():
      interface.close()
      gradio_thread.join(timeout=1)

  load_dotenv()

  node_manager = NodeManager(
    vtn_name=os.getenv('VTN_NAME', 'default_vtn'),
    vtn_path_prefix=os.getenv('VTN_PATH_PREFIX', '/0/OpenADR2/Simple/2.0b'),
  )
  app = AsyncGradioApp(slider_file='./slider_values.txt')
  interface = app.create_interface()

  gradio_thread = threading.Thread(
    target=run_gradio_thread, args=(interface,), daemon=True
  )
  gradio_thread.start()

  try:
    node_manager.run_node()
  finally:
    cleanup()


if __name__ == '__main__':
  main()
