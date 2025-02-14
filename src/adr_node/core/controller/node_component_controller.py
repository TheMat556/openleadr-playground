from typing import List

from src.adr_node.communication.rest.exceptions.rest_service_exception import (
  RestServiceException,
)
from src.adr_node.core.interfaces.irunable import IRunnable
from src.adr_node.core.controller.thread_controller import ThreadController
from src.adr_node.core.interfaces.inode_controller import IComponentController
from src.openadr_node.adr_logger.logger import logger


class NodeComponentController(IComponentController):
  """
  Controller for managing node components.

  This class is responsible for starting and stopping runnable services
  using a thread controller.
  """

  def __init__(self, runnable_services: List[IRunnable]):
    """
    Initialize the NodeComponentController.

    Args:
        runnable_services (List[IRunnable]): List of services that implement the IRunnable interface.
    """
    self._thread_controller = ThreadController()
    self._runnable_services = runnable_services
    self._is_running = False

  def start(self) -> None:
    """
    Start all runnable services.

    This method starts each service in a separate thread and sets the running state to True.
    """
    try:
      for service in self._runnable_services:
        self._thread_controller.start_thread(service.run, service.__class__.__name__)

      self._is_running = True
      logger.info('NodeComponentController started successfully.')
    except RestServiceException as e:
      logger.error(f'Failed to start NodeComponentController: {str(e)}')
      raise

  def stop(self) -> None:
    """
    Stop all runnable services.

    This method stops all services and sets the running state to False.
    """
    if self._is_running:
      try:
        self._is_running = False
        logger.info('NodeComponentController stopped successfully.')
      except RestServiceException as e:
        logger.error(f'Failed to stop NodeComponentController: {str(e)}')
        raise

  def __del__(self):
    """
    Cleanup method called when the instance is being destroyed.
    """
    logger.info('NodeComponentController instance has been cleaned up.')
