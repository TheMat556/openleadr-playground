from src.adr_node.communication.rest.exceptions.rest import RestServiceException
from src.adr_node.communication.rest.interfaces.irest_service import IRestService
from src.adr_node.core.services.adr.interfaces.iadr_service import IAdrService
from src.adr_node.core.controller.thread_controller import ThreadController
from src.adr_node.core.interfaces.inode_controller import IComponentController
from src.openadr_node.adr_logger.logger import logger


class NodeComponentController(IComponentController):
  def __init__(
    self, rest_service: IRestService, adr_service: IAdrService
  ):  # Changed to match container
    """
    Initialize the NodeController.

    Args:
        rest_service: The REST service instance
    """
    self._thread_controller = ThreadController()

    self.rest_service = rest_service
    self.adr_service = adr_service

    self.adr_service.create_node_tasks()
    self._running = False

    logger.info('NodeController instance created with REST service.')

  def start(self) -> None:
    try:
      self._thread_controller.start_thread(self.adr_service.run, 'ADR Service')
      self._thread_controller.start_thread(self.rest_service.start, 'REST Service')

      self._running = True
      logger.info('NodeController started successfully.')
    except RestServiceException as e:
      logger.error(f'Failed to start node controller: {str(e)}')
      raise

  def stop(self) -> None:
    if self._running:
      try:
        self.rest_service.stop()
        self._running = False
        logger.info('NodeController stopped successfully.')
      except RestServiceException as e:
        logger.error(f'Failed to stop node controller: {str(e)}')
        raise

  def __del__(self):
    """Cleanup method called when the instance is being destroyed."""
    logger.info('NodeController instance has been cleaned up.')
