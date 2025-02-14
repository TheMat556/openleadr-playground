from src.adr_node.core.dependency_injection.container import Container
from src.adr_node.intermediate_node.config.intermediate_node_config import (
  IntermediateNodeConfig,
)
from src.openadr_node import logger


class IntermediateNode:
  def __init__(self, config: IntermediateNodeConfig):
    self.config = config
    self._container, self._component_controller = self._setup_node()

  def _setup_node(self):
    return Container.create(self.config.to_application_config())

  def run(self) -> None:
    try:
      print('Starting intermediate node component controller')
      self._component_controller.start()
    except Exception as e:
      logger.error(f'Error running intermediate node: {e}')
      raise
