import asyncio
import sys
from typing import Optional, List, Any, Dict, Callable

from src.openadr_node import logger
from src.openadr_node.adr_base_config import AdrBaseConfig
from src.openadr_node.node_resource_controller import NodeResourceController
from src.openadr_node.database.database_manager import DatabaseManager
from src.openadr_node.database.loadprofile_manager import LoadProfileManager
from src.openadr_node.node_dispatcher_controller import NodeDispatcherController
from src.openadr_node.models import ReportConfiguration
from src.openadr_node.models.event import ResourceConsumption
from src.openadr_node.models.mqtt_config import MQTTConfig
from src.openadr_node.models.rest_config import RestApiConfig
from src.openadr_node.protocols import RestApiManager
from src.openadr_node.protocols.mqtt_manager import MQTTManager
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
    Initialize the NodeManager with the given configuration.
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
    self._dispatcher_manager = NodeDispatcherController(self)

    self._loop = asyncio.get_event_loop()
    self._node_task_manager = NodeOpenADRController(
      self._loop,
      vtn_name=self._vtn_name,
      ven_name=self._ven_name,
      vtn_url=self._vtn_url,
      openadr_http_host=self._openadr_http_host,
      openadr_http_port=self._openadr_http_port,
      openadr_vtn_path_prefix=self._openadr_vtn_path_prefix,
    )
    self._node_task_manager.create_node_tasks()

    self._subscribers: Dict[str, List[Callable]] = {}
    self._ven_data: Dict[str, Dict[str, float]] = {}
    self._current_consumption = 0.0
    self._load_profile_manager = None
    self._thread_manager = NodeThreadController()

    if node_id:
      self._load_profile_manager = LoadProfileManager(DatabaseManager(f'{node_id}.db'))

    if self._load_profile_manager:
      self._data_updater = NodeResourceController(self._load_profile_manager)

    if self._rest_api_config:
      self._initialize_rest_api_manager(self._rest_api_config)

    if self._mqtt_config:
      self._initialize_mqtt_manager(self._mqtt_config)

    dispatcher.send(signal='on_ready', sender='system')

  def _initialize_rest_api_manager(self, config: RestApiConfig) -> None:
    """
    Initialize the REST API manager.
    """
    if not config.port:
      logger.warning(
        'Incomplete REST API configuration provided. REST API manager will not be initialized.'
      )
      return
    self._rest_api = RestApiManager(config.port)
    try:
      self._rest_api.set_load_profile_manager(self._load_profile_manager)
      self._rest_api.init_routes(self._rest_api)
      self._start_rest_api_thread()
    except Exception as e:
      logger.error(f'Failed to initialize REST API manager: {e}')
      self._rest_api = None

  def _start_rest_api_thread(self) -> None:
    """
    Start the REST API server in a separate thread.
    """
    self._thread_manager.start_thread(target=self._rest_api.run, name='RestApiThread')

  def _initialize_mqtt_manager(self, config: MQTTConfig) -> None:
    """
    Initialize the MQTT manager.
    """
    if config.is_valid():
      self._mqtt_manager = MQTTManager(
        broker=config.broker,
        port=config.port,
        topic_load_profile=config.topic_load_profile,
        topic_consumption=config.topic_consumption,
        load_profile_manager=self._load_profile_manager,
        username=config.username,
        password=config.password,
      )
      self._mqtt_manager.start()
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
      target=self._mqtt_manager.client.loop_forever, name='MQTTLoopThread'
    )
    self._thread_manager.start_thread(
      target=self._mqtt_manager.publish_load_profile, name='PublishThread'
    )

  def _register_dispatcher(self, sender: str, signal: str, data: str) -> None:
    """
    Register a dispatcher for a signal.
    """
    self._dispatcher_manager.register_dispatcher(sender, signal, data)

  def _on_update_load_profile(self, sender: str, data: List[Dict[str, Any]]) -> None:
    """
    Handle the update load profile signal.
    """
    self._data_updater.update_load_profile(sender, data)

  def _on_update_consumption_data(self, sender: str, data: ResourceConsumption) -> None:
    """
    Handle the update consumption data signal.
    """
    self._data_updater.update_consumption_data(sender, data)

  def add_task(self, task: Callable) -> None:
    """
    Add a task to the event loop.
    """
    self._loop.create_task(task())

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
      self._node_task_manager.add_report(list_of_reports)
    except Exception as e:
      logger.error(f'Error adding report: {e}')

  def publish(self, signal: str, data: Any) -> None:
    """
    Publish a signal to subscribers.
    """
    self._node_task_manager.publish(signal, data)

  def subscribe(self, signal: str, callback: Callable) -> None:
    """
    Subscribe to a signal.
    """
    self._node_task_manager.subscribe(signal, callback)
