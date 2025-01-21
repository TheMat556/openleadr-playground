import asyncio
from datetime import timedelta
from typing import Optional, List, Any, Dict

from injector import inject

from src.openadr_node import logger
from src.openadr_node.config import AdrBaseConfig
from src.openadr_node.config.app_config import ApplicationConfig
from src.openadr_node.database.interfaces.database_interface import (
  IEnergyDatabaseController,
  IRestAPIController,
)
from src.openadr_node.models import ReportConfiguration
from src.openadr_node.mqtt_controller import MQTTManager
from src.openadr_node.node_dispatcher_controller import NodeDispatcherController
from src.openadr_node.node_open_adr_controller import NodeOpenADRController
from src.openadr_node.node_resource_controller import NodeResourceController
from src.openadr_node.node_thread_controller import NodeThreadController


class NodeController(AdrBaseConfig):
  @inject
  def __init__(
    self,
    config: ApplicationConfig,
    energy_db_controller: IEnergyDatabaseController,
    rest_controller: Optional[IRestAPIController],
    mqtt_controller: Optional[MQTTManager],
    resource_controller: NodeResourceController,
    dispatcher_controller: NodeDispatcherController,
    thread_controller: NodeThreadController,
    open_adr_controller: NodeOpenADRController,
  ):
    """Initialize NodeController with injected dependencies"""
    dispatcher_controller.set_node_controller(self)
    super().__init__()
    self.config = config
    self.energy_db_controller = energy_db_controller
    self.rest_controller = rest_controller
    self.mqtt_controller = mqtt_controller
    self.resource_controller = resource_controller
    self.dispatcher_controller = dispatcher_controller
    self.thread_controller = thread_controller
    self.open_adr_controller = open_adr_controller

    self._periodic_tasks = []
    self._loop = asyncio.get_event_loop()

    self._setup_controllers()

  def _setup_controllers(self) -> None:
    """Initialize and setup all controllers"""
    try:
      # Initialize OpenADR tasks
      # self.open_adr_controller.create_node_tasks()

      # Start REST API if configured
      # if self.rest_controller:
      #   self.thread_controller.start_thread(
      #     target=self.rest_controller.serve_forever, name='RestApiThread'
      #   )

      # Start MQTT if configured
      # if self.mqtt_controller:
      #   self.mqtt_controller.start()
      #   self.thread_controller.start_thread(
      #     target=lambda: asyncio.run(self.mqtt_controller._publish_loop()),
      #     name='MqttPublishThread',
      #   )

      logger.info('All controllers initialized successfully')
    except Exception as e:
      logger.error(f'Failed to setup controllers: {e}')
      raise

  async def run(self) -> None:
    """Run the node controller"""
    try:
      logger.info('Starting NodeController...')
      await self._run_forever()
    except Exception as e:
      logger.error(f'Error in NodeController: {e}')
      raise
    finally:
      self.cleanup()

  async def _run_forever(self) -> None:
    """Run the event loop forever"""
    try:
      await self._loop.create_task(self._keep_alive())
    except asyncio.CancelledError:
      logger.info('NodeController shutdown requested')
    except Exception as e:
      logger.error(f'Error in event loop: {e}')
      raise

  async def _keep_alive(self) -> None:
    """Keep the application alive and handle periodic health checks"""
    while True:
      await asyncio.sleep(1)  # Adjust sleep time as needed
      # Add health checks or periodic maintenance here

  def cleanup(self) -> None:
    """Cleanup resources and shutdown controllers"""
    try:
      logger.info('Starting cleanup...')
      self.cancel_periodic_tasks()

      if self.rest_controller:
        self.rest_controller.shutdown()

      if self.mqtt_controller:
        self.mqtt_controller.stop()

      self.thread_controller.stop_all_threads()
      logger.info('Cleanup completed successfully')
    except Exception as e:
      logger.error(f'Error during cleanup: {e}')
      raise

  def start_periodic_task(self, method: Any, interval: timedelta) -> None:
    """Start a periodic task"""
    interval_seconds = interval.total_seconds()
    task = self._loop.create_task(
      self._trigger_method_periodically(
        method, interval_seconds, first_interval=4 / 3 * interval_seconds
      )
    )
    self._periodic_tasks.append(task)

  def cancel_periodic_tasks(self) -> None:
    """Cancel all periodic tasks"""
    for task in self._periodic_tasks:
      task.cancel()
    self._periodic_tasks.clear()

  @staticmethod
  async def _trigger_method_periodically(
    method: Any, interval: float, first_interval: float
  ) -> None:
    """Trigger a method periodically"""
    await asyncio.sleep(first_interval)
    while True:
      try:
        method()
        await asyncio.sleep(interval)
      except Exception as e:
        logger.error(f'Error in periodic task: {e}')
        await asyncio.sleep(interval)

  def add_report(
    self, list_of_reports: Optional[List[ReportConfiguration]] = None
  ) -> None:
    """Add reports to OpenADR controller"""
    try:
      self.open_adr_controller.add_reports(list_of_reports)
    except Exception as e:
      logger.error(f'Error adding reports: {e}')
      raise

  def _on_update_load_profile(self, sender: str, data: List[Dict[str, Any]]) -> None:
    """Handle load profiler update signal"""
    self.resource_controller.update_load_profile(sender, data)

  def _on_update_consumption_data(self, sender: str, data: Any) -> None:
    """Handle consumption data update signal"""
    print('_on_update_consumption_data', data)
    self.resource_controller.update_consumption_data(sender, data)

  def _on_register_report(self, sender: str, data: str) -> None:
    """Handle report registration signal"""
    self.resource_controller.on_register_report(data)
