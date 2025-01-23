from src.adr_node.core.dependency_injection.container import Container
from src.adr_node.mock_node.config.mock_node_config import MockNodeConfig


class MockNode:
  def __init__(self, config: MockNodeConfig):
    self.config = config
    print('config', self.config)
    self._component_controller = self._setup_node()

  def _setup_node(self):
    container = Container.create(self.config.to_application_config())
    return container.node_component_controller()

  def _setup_gradio(self):
    pass

  def run(self) -> None:
    # self._component_controller.start()
    try:
      self._component_controller.start()
    except Exception as _:
      # logger.error(f'Error running node: {e}')
      raise
