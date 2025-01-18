import asyncio
import sys
import uuid
from datetime import timedelta
from typing import Optional, List, Any, Dict, Callable

from src.openadr_node import logger
from src.openadr_node.adr_base_config import AdrBaseConfig
from src.openadr_node.node_resource_controller import NodeResourceController
from src.openadr_node.database.database_manager import DatabaseManager
from src.openadr_node.database.energy_database_controller import (
  EnergyDatabaseController,
)
from src.openadr_node.node_dispatcher_controller import NodeDispatcherController
from src.openadr_node.models import ReportConfiguration
from src.openadr_node.models.event import ResourceConsumption
from src.openadr_node.models.mqtt_config import MQTTConfig
from src.openadr_node.models.rest_config import RestApiConfig
from src.openadr_node.protocols import RestAPIController
from src.openadr_node.protocols.mqtt_controller import MQTTController
from src.openadr_node.node_thread_controller import NodeThreadController
from src.openadr_node.node_open_adr_controller import NodeOpenADRController
from pydispatch import dispatcher


class NodeController(AdrBaseConfig):
  """
  Manages the Virtual Top Node (VTN) and Virtual End Node (VEN) and handles communication between them.
  """

  def __init__(
    self,
    node_id: Optional[str] = None,
    vtn_name: Optional[str] = None,
    ven_name: Optional[str] = None,
    vtn_url: Optional[str] = None,
    openadr_http_host: Optional[str] = None,
    openadr_http_port: Optional[int] = None,
    openadr_vtn_path_prefix: Optional[str] = None,
    mqtt_config: Optional[MQTTConfig] = None,
    rest_api_config: Optional[RestApiConfig] = None,
  ):
    """
    Initialize the NodeController with the given configuration.

    Parameters
    ----------
    node_id : Optional[str]
        The ID of the node.
    vtn_name : Optional[str]
        Name of the Virtual Top Node (VTN).
    ven_name : Optional[str]
        Name of the Virtual End Node (VEN).
    vtn_url : Optional[str]
        URL of the VTN.
    openadr_http_host : Optional[str]
        HTTP host for OpenADR.
    openadr_http_port : Optional[int]
        HTTP port for OpenADR.
    openadr_vtn_path_prefix : Optional[str]
        Path prefix for the VTN.
    mqtt_config : Optional[MQTTConfig]
        Configuration for MQTT.
    rest_api_config : Optional[RestApiConfig]
        Configuration for REST API.
    """
    super().__init__()
    self._vtn_name = vtn_name
    self._vtn_url = vtn_url
    self._ven_name = ven_name
    self._openadr_http_host = openadr_http_host
    self._openadr_http_port = openadr_http_port
    self._openadr_vtn_path_prefix = openadr_vtn_path_prefix
    self._mqtt_config = mqtt_config
    self._rest_api_config = rest_api_config

    self._subscribers: Dict[str, List[Callable]] = {}
    self._ven_data: Dict[str, Dict[str, float]] = {}
    self._current_consumption = 0.0
    self._energy_database_controller = None

    self._dispatcher_manager = NodeDispatcherController(self)
    self._thread_manager = NodeThreadController()

    self._periodic_tasks = []
    self._loop = asyncio.get_event_loop()

    database_id = node_id or str(uuid.uuid4())
    self._energy_database_controller = EnergyDatabaseController(
      DatabaseManager(f'{database_id}.db')
    )

    if self._energy_database_controller:
      self.node_resource_controller = NodeResourceController(
        self._energy_database_controller
      )
      self.start_periodic_task(
        lambda: self.node_resource_controller.update_load_profile(
          '', None, use_z_directly=False
        ),
        timedelta(minutes=1),
      )
    if self._rest_api_config:
      self._initialize_rest_api_manager(self._rest_api_config)

    if self._mqtt_config:
      self._initialize_mqtt_controller(self._mqtt_config)

    self._node_task_manager = NodeOpenADRController(
      self._loop,
      vtn_name=self._vtn_name,
      ven_name=self._ven_name,
      vtn_url=self._vtn_url,
      openadr_http_host=self._openadr_http_host,
      openadr_http_port=self._openadr_http_port,
      openadr_vtn_path_prefix=self._openadr_vtn_path_prefix,
    )
    self.create_node_tasks()

    dispatcher.send(signal='on_ready', sender='system')

  def __del__(self):
    """
    Ensure all resources are cleaned up when the instance is destroyed.
    """
    self.cancel_periodic_tasks()
    if hasattr(self, '_rest_api') and self._rest_api:
      self._rest_api.shutdown()
    if hasattr(self, '_mqtt_controller') and self._mqtt_controller:
      self._mqtt_controller.stop()
    logger.info('NodeController instance has been cleaned up.')

  def create_node_tasks(self) -> None:
    """
    Create and start tasks for the VTN and VEN nodes.
    """
    try:
      self._node_task_manager.create_node_tasks()
      logger.info('Node tasks created successfully')
    except Exception as e:
      logger.error(f'Failed to create node tasks: {e}')
      raise

  def _initialize_rest_api_manager(self, config: RestApiConfig) -> None:
    """
    Initialize the REST API manager.

    Parameters
    ----------
    config : RestApiConfig
        Configuration for REST API.
    """
    if not config.port:
      logger.warning(
        'Incomplete REST API configuration provided. REST API manager will not be initialized.'
      )
      return
    try:
      self._rest_api = RestAPIController(config.port)
      self._rest_api.set_load_profile_manager(self._energy_database_controller)
      self._rest_api.init_routes(self._rest_api)
      self._start_rest_api_thread()
    except Exception as e:
      logger.error(f'Failed to initialize REST API manager: {e}')
      self._rest_api = None

  def _start_rest_api_thread(self) -> None:
    """
    Start the REST API server in a separate thread.
    """
    self._thread_manager.start_thread(
      target=self._rest_api.serve_forever, name='RestApiThread'
    )

  def _initialize_mqtt_controller(self, config: MQTTConfig) -> None:
    """
    Initialize the MQTT manager.

    Parameters
    ----------
    config : MQTTConfig
        Configuration for MQTT.
    """
    if config.is_valid():
      self._mqtt_controller = MQTTController(
        config=config,
        energy_database_controller=self._energy_database_controller,
        ven_id=self._ven_name,
      )
      self._mqtt_controller.start()
      self._start_mqtt_threads()
    else:
      logger.warning(
        'Incomplete MQTT configuration provided. MQTT manager will not be initialized.'
      )

  def _start_mqtt_threads(self) -> None:
    """
    Start the MQTT client and associated threads.
    """
    self._thread_manager.start_thread(
      target=self._mqtt_controller.publish_load_profile, name='PublishThread'
    )

  def _register_dispatcher(self, sender: str, signal: str, data: str) -> None:
    """
    Register a dispatcher for a signal.

    Parameters
    ----------
    sender : str
        The sender of the signal.
    signal : str
        The signal to register.
    data : str
        The data associated with the signal.
    """
    self._dispatcher_manager.register_dispatcher(sender, signal, data)

  def _on_update_load_profile(self, sender: str, data: List[Dict[str, Any]]) -> None:
    """
    Handle the update load profile signal.

    Parameters
    ----------
    sender : str
        The sender of the signal.
    data : List[Dict[str, Any]]
        The data associated with the signal.
    """
    if hasattr(self, 'node_resource_controller') and self.node_resource_controller:
      self.node_resource_controller.update_load_profile(sender, data)

  def _on_update_consumption_data(self, sender: str, data: ResourceConsumption) -> None:
    """
    Handle the update consumption data signal.

    Parameters
    ----------
    sender : str
        The sender of the signal.
    data : ResourceConsumption
        The data associated with the signal.
    """
    if hasattr(self, 'node_resource_controller') and self.node_resource_controller:
      self.node_resource_controller.update_consumption_data(sender, data)

  def _on_register_report(self, sender: str, data: str) -> None:
    """
    Handle the register report signal.

    Parameters
    ----------
    sender : str
        The sender of the signal.
    data : str
        The data associated with the signal.
    """
    if hasattr(self, 'node_resource_controller') and self.node_resource_controller:
      self.node_resource_controller.on_register_report(data)

  def add_task(self, task: Callable) -> None:
    """
    Add a task to the event loop.

    Parameters
    ----------
    task : Callable
        The task to be added.
    """
    self._loop.create_task(task())

  def start_periodic_task(self, method: Callable, interval: timedelta) -> None:
    """
    Start a periodic task to trigger a method at a specified interval.

    Parameters
    ----------
    method : Callable
        The method to be triggered.
    interval : timedelta
        The interval at which to trigger the method.
    """
    interval_seconds = interval.total_seconds()
    task = self._loop.create_task(
      self._trigger_method_periodically(
        method, interval_seconds, first_interval=4 / 3 * interval_seconds
      )
    )
    if not hasattr(self, '_periodic_tasks'):
      self._periodic_tasks = []
    self._periodic_tasks.append(task)

  def cancel_periodic_tasks(self) -> None:
    """
    Cancel all periodic tasks.
    """
    if hasattr(self, '_periodic_tasks'):
      for task in self._periodic_tasks:
        task.cancel()
      self._periodic_tasks.clear()

  @staticmethod
  async def _trigger_method_periodically(
    method: Callable, interval: float, first_interval: float
  ) -> None:
    """
    Trigger a method at a specified interval without blocking execution.

    Parameters
    ----------
    method : Callable
        The method to be triggered.
    interval : float
        The interval in seconds at which to trigger the method.
    first_interval : float
        The interval in seconds to defer the first call.
    """
    await asyncio.sleep(first_interval)
    while True:
      method()
      await asyncio.sleep(interval)

  def run_node(self) -> None:
    """
    Run the node event loop.
    """
    try:
      self._loop.run_forever()
    except Exception as e:
      logger.error(f'Error running node: {e}')
      sys.exit(1)

  def add_report(
    self, list_of_reports: Optional[List[ReportConfiguration]] = None
  ) -> None:
    """
    Add a report to the VEN.

    Parameters
    ----------
    list_of_reports : Optional[List[ReportConfiguration]]
        List of report configurations.
    """
    try:
      logger.debug(f'Adding reports: {list_of_reports}')
      self._node_task_manager.add_reports(list_of_reports)
      logger.info('Reports added successfully')
    except Exception as e:
      logger.error(f'Error adding report: {e}', exc_info=True)
      raise RuntimeError(f'Failed to add reports: {e}') from e

  def publish(self, signal: str, data: Any) -> None:
    """
    Publish a signal to subscribers.

    Parameters
    ----------
    signal : str
        The signal to publish.
    data : Any
        The data associated with the signal.
    """
    try:
      self._node_task_manager.publish(signal, data)
    except Exception as e:
      logger.error(f'Failed to publish signal {signal}: {e}')
      raise

  def subscribe(self, signal: str, callback: Callable) -> None:
    """
    Subscribe to a signal.

    Parameters
    ----------
    signal : str
        The signal to subscribe to.
    callback : Callable
        The callback to be executed when the signal is received.
    """
    try:
      self._node_task_manager.subscribe(signal, callback)
    except Exception as e:
      logger.error(f'Failed to subscribe to signal {signal}: {e}')
      raise
