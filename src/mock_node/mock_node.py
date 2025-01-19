import threading
from injector import Injector
import logging

from src.mock_node.config.mock_node_config import MockNodeConfig
from src.openadr_node.di.modules import ApplicationModule
from src.openadr_node.node_controller import NodeController
from src.mock_node.addons.gradio_ui.async_gradio_app import AsyncGradioApp

logger = logging.getLogger(__name__)


class MockNode:
  def __init__(self, config: MockNodeConfig):
    self.config = config
    self._setup_node()
    self._setup_gradio()

  def _setup_node(self) -> None:
    app_config = self.config.to_application_config()
    injector = Injector([ApplicationModule(app_config)])
    self.node = injector.get(NodeController)

  def _setup_gradio(self) -> None:
    self.app = AsyncGradioApp(slider_file=self.config.slider_file)
    self.interface = self.app.create_interface()

  def _run_gradio(self) -> None:
    try:
      self.interface.launch(
        server_port=self.config.gradio_port, server_name=self.config.gradio_host
      )
    except Exception as e:
      logger.error(f'Failed to launch Gradio interface: {e}')

  async def run(self) -> None:
    gradio_thread = threading.Thread(target=self._run_gradio, daemon=True)
    gradio_thread.start()

    try:
      print('running mock node')
      await self.node.run()
    finally:
      if self.interface and gradio_thread.is_alive():
        self.interface.close()
        gradio_thread.join(timeout=1)
