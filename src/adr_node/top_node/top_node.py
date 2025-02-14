from src.adr_node.core.dependency_injection.container import Container
from src.adr_node.top_node.config.top_node_config import TopNodeConfig
from src.openadr_node import logger


class TopNode:
  def __init__(self, config: TopNodeConfig):
    self.config = config
    self._component_controller, self._component_controller = self._setup_node()

  def _setup_node(self):
    return Container.create(self.config.to_application_config())

  def _setup_gradio(self):
    pass

  def run(self) -> None:
    try:
      print('Starting node component controller')
      self._component_controller.start()
    except Exception as e:
      logger.error(f'Error running node: {e}')
      raise
