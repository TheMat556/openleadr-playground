import logging

from src.adr_node.core.dependency_injection.container import Container
from src.tier_nodes.top_node.config.top_node_config import TopNodeConfig


class TopNode:
  """
  TopNode class to manage the configuration and execution of the top node.

  :param config: Configuration for the top node.
  :type config: TopNodeConfig
  """

  def __init__(self, config: TopNodeConfig):
    self.config = config
    self._container, self._component_controller = self._setup_node()

  def _setup_node(self):
    """
    Set up the node by creating the container and component controller.

    :return: Tuple containing the container and component controller.
    :rtype: Tuple[Container, Any]
    """
    return Container.create(self.config.to_application_config())

  def run(self) -> None:
    """
    Run the top node by starting the component controller.

    :raises Exception: If an error occurs while running the node.
    """
    try:
      print('Starting node component controller')
      self._component_controller.start()
    except Exception as e:
      logging.error(f'Error running node: {e}')
      raise
