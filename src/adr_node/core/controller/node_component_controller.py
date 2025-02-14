from typing import List

from src.adr_node.communication.rest.exceptions.rest_service_exception import (
  RestServiceException,
)
from src.adr_node.core.interfaces.irunable import IRunnable
from src.adr_node.core.controller.thread_controller import ThreadController
from src.adr_node.core.interfaces.inode_controller import IComponentController
from src.openadr_node.adr_logger.logger import logger


class NodeComponentController(IComponentController):
  def __init__(self, runnable_services=List[IRunnable]):
    """
    Initialize the NodeController.

    Args:
        rest_service: The REST service instance
    """
    self._thread_controller = ThreadController()
    self._runnable_services = runnable_services
    self._running = False

  def start(self) -> None:
    try:
      for runnable_service in self._runnable_services:
        self._thread_controller.start_thread(
          runnable_service.run, runnable_service.__class__.__name__
        )

      self._running = True
      logger.info('NodeController started successfully.')
    except RestServiceException as e:
      logger.error(f'Failed to start node controller: {str(e)}')
      raise

  def stop(self) -> None:
    if self._running:
      try:
        self._running = False
        logger.info('NodeController stopped successfully.')
      except RestServiceException as e:
        logger.error(f'Failed to stop node controller: {str(e)}')
        raise

  def __del__(self):
    """Cleanup method called when the instance is being destroyed."""
    logger.info('NodeController instance has been cleaned up.')
