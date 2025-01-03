import asyncio
import sys
from datetime import datetime, timezone
from typing import Optional, List, Any, Dict, Callable

from src.openadr_node import logger
from src.openadr_node.adr_base_config import AdrBaseConfig
from src.openadr_node.database.database_manager import DatabaseManager
from src.openadr_node.database.loadprofile_manager import LoadProfileManager
from src.openadr_node.models import ReportConfiguration
from src.openadr_node.models.event import ResourceConsumption
from src.openadr_node.protocols.mqtt_manager import MQTTManager
from src.openadr_node.virtual_end_node import VirtualEndNode
from src.openadr_node.virtual_top_node import VirtualTopNode
from src.openadr_node.protocols import RestApiManager

from pydispatch import dispatcher


class NodeManager(AdrBaseConfig):
  """
  Manages the Virtual Top Node (VTN) and Virtual End Node (VEN) and handles communication between them.
  """

  def __init__(
    self,
    node_id: Optional[str] = None,
    vtn_name: Optional[str] = None,
    ven_name: Optional[str] = None,
    vtn_url: Optional[str] = None,
    http_host: Optional[str] = None,
    http_port: Optional[int] = None,
    vtn_path_prefix: Optional[str] = None,
    rest_api_port: Optional[int] = None,
    mqtt_broker: Optional[str] = None,
    mqtt_port: Optional[int] = None,
    mqtt_topic_load_profile: Optional[str] = None,
    mqtt_topic_consumption: Optional[str] = None,
    mqtt_username: Optional[str] = None,
    mqtt_password: Optional[str] = None,
  ):
    """
    Initialize the NodeManager.

    :param vtn_name: Name of the Virtual Top Node.
    :type vtn_name: Optional[str]
    :param ven_name: Name of the Virtual End Node.
    :type ven_name: Optional[str]
    :param vtn_url: URL of the Virtual Top Node.
    :type vtn_url: Optional[str]
    :param http_host: HTTP host for the server.
    :type http_host: Optional[str]
    :param http_port: HTTP port for the server.
    :type http_port: Optional[int]
    :param vtn_path_prefix: Path prefix for the VTN.
    :type vtn_path_prefix: Optional[str]
    :param rest_api_port: Port for the REST API.
    :type rest_api_port: Optional[int]
    :param mqtt_broker: MQTT broker address.
    :type mqtt_broker: Optional[str]
    :param mqtt_port: MQTT broker port.
    :type mqtt_port: Optional[int]
    :param mqtt_topic_load_profile: MQTT topic for load profile.
    :type mqtt_topic_load_profile: Optional[str]
    :param mqtt_topic_consumption: MQTT topic for consumption.
    :type mqtt_topic_consumption: Optional[str]
    :param mqtt_username: MQTT username.
    :type mqtt_username: Optional[str]
    :param mqtt_password: MQTT password.
    :type mqtt_password: Optional[str]
    """
    super().__init__()
    self._vtn_name = vtn_name
    self._vtn_url = vtn_url
    self._ven_name = ven_name
    self._http_host = http_host
    self._http_port = http_port
    self._vtn_path_prefix = vtn_path_prefix
    self._rest_api_port = rest_api_port

    self._ven = None
    self._vtn = None

    self._loop = asyncio.get_event_loop()
    self._create_node_tasks()
    self._subscribers: Dict[str, List[Callable]] = {}
    self._ven_data: Dict[str, Dict[str, float]] = {}
    self._current_consumption = 0

    self._rest_api = RestApiManager(self._rest_api_port)

    if node_id:
      self._load_profile_manager = LoadProfileManager(DatabaseManager(node_id + '.db'))
      if self._rest_api_port:
        self._rest_api = RestApiManager(self._rest_api_port)
        self._rest_api.set_load_profile_manager(self._load_profile_manager)
        self._rest_api.init_routes(self._rest_api)
        self._rest_api.start()

      if (
        mqtt_broker
        and mqtt_port
        and mqtt_topic_load_profile
        and mqtt_topic_consumption
        and mqtt_username
        and mqtt_password
      ):
        self._mqtt_manager = MQTTManager(
          broker=mqtt_broker,
          port=mqtt_port,
          topic_load_profile=mqtt_topic_load_profile,
          topic_consumption=mqtt_topic_consumption,
          load_profile_manager=self._load_profile_manager,
          username=mqtt_username,
          password=mqtt_password,
        )
        self._mqtt_manager.start()

    dispatcher.send(signal='on_ready', sender='system')

  def get_method(self, signal: str) -> Optional[Callable]:
    """
    Get the method associated with a signal.

    :param signal: The signal name.
    :type signal: str
    :return: The method associated with the signal.
    :rtype: Optional[Callable]
    """
    method_name = f'_on_{signal}'
    return getattr(self, method_name, None)

  def _register_dispatcher(self, sender: str, signal: str, data: str) -> None:
    """
    Register a dispatcher for a signal.

    :param sender: The sender of the signal.
    :type sender: str
    :param signal: The signal name.
    :type signal: str
    :param data: The data associated with the signal.
    :type data: str
    """
    method = self.get_method(data)
    if callable(method):
      dispatcher.connect(self._call_method, signal=data, sender=dispatcher.Any)
    else:
      dispatcher.connect(self._forward_dispatcher, signal=data, sender=sender)

    logger.info(f'NM - Connected _on{signal} to signal: {data} with sender: {sender}')

  @staticmethod
  def _forward_dispatcher(sender: str, signal: str, data: Any) -> None:
    """
    Forward a dispatcher signal.

    :param sender: The sender of the signal.
    :type sender: str
    :param signal: The signal name.
    :type signal: str
    :param data: The data associated with the signal.
    :type data: Any
    """
    dispatcher.send(signal=signal, sender='nm', data=data)

  def _call_method(self, sender: str, signal: str, data: Any) -> None:
    """
    Call the method associated with a signal.

    :param sender: The sender of the signal.
    :type sender: str
    :param signal: The signal name.
    :type signal: str
    :param data: The data associated with the signal.
    :type data: Any
    """
    if sender == 'nm':
      return

    method = self.get_method(signal)
    if callable(method):
      try:
        method(sender, data)
      except Exception as e:
        logger.error(f'Error calling method {signal}: {e}')
        raise

  def _on_update_load_profile(self, sender: str, data: List[Dict[str, Any]]) -> None:
    """
    Update the load profile.

    :param sender: The sender of the signal.
    :type sender: str
    :param data: The data associated with the signal.
    :type data: List[Dict[str, Any]]
    """
    if not isinstance(data, list):
      logger.error('Invalid data format: expected list of intervals')
      return

    transformed_data = [
      {
        'dstart': int(interval['dtstart'].timestamp() * 1000),
        'duration': int(interval['duration'].total_seconds() * 1000),
        'signal_payload': interval['signal_payload'],
      }
      for interval in data
    ]

    self._load_profile_manager.insert_load_profile(transformed_data)

    dispatcher.send(sender='nm', signal='update_load_profile', data=transformed_data)

  def _on_update_consumption_data(self, sender: str, data: ResourceConsumption) -> None:
    """
    Update current consumption and refresh the label if it exists.

    :param sender: Signal sender.
    :type sender: str
    :param data: Consumption data dictionary.
    :type data: ResourceConsumption
    :raises AttributeError: If an attribute is missing.
    :raises IndexError: If an index is out of range.
    """
    if self._vtn and sender == 'ven':
      return

    try:
      self._current_consumption = 0.0
      if data.ven_id not in self._ven_data:
        self._ven_data[data.ven_id] = {}
      self._ven_data[data.ven_id][data.resource_id] = data.data[1]
      for ven_id, resources in self._ven_data.items():
        for resource_id, value in resources.items():
          self._current_consumption += value

      timestamp_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
      consumption_data = {
        'timestamp': timestamp_ms,
        'ven_id': data.ven_id,
        'resource_id': data.resource_id,
        'value': data.data[1],
      }
      self._load_profile_manager.insert_consumption(consumption_data)

      logger.debug(f'Updated consumption data - Total: {self._current_consumption}')
      dispatcher.send(
        sender='nm', signal='update_consumption_data', data=self._current_consumption
      )
    except (AttributeError, IndexError) as e:
      logger.error(f'Error processing consumption data: {e}')
      raise

  def _create_node_tasks(self) -> None:
    """
    Create tasks for the VTN and VEN nodes.
    """

    async def run_with_notification(
      coro: Callable,
      start_callback: Optional[Callable[[], None]],
      end_callback: Optional[Callable[[], None]],
    ) -> None:
      if start_callback:
        start_callback()
      await coro
      if end_callback:
        end_callback()

    if self._vtn_name:
      self._vtn = VirtualTopNode(
        server_name=self._vtn_name,
        http_host=self._http_host,
        http_port=self._http_port,
        path_prefix=self._vtn_path_prefix,
      )
      self._loop.create_task(
        run_with_notification(
          self._vtn.get_open_adr_server_run(),
          start_callback=lambda: logger.info('VTN task started'),
          end_callback=lambda: self.publish('vtn_created', {'status': 'created'}),
        )
      )

    if self._ven_name and self._vtn_url:
      self._ven = VirtualEndNode(self._ven_name, self._vtn_url)

      self._register_base_report()

      self._loop.create_task(
        run_with_notification(
          self._ven.get_open_adr_server_run(),
          start_callback=lambda: logger.info('VEN task started'),
          end_callback=lambda: logger.info('VEN task finished'),
        )
      )

  def _register_base_report(self) -> None:
    """
    Register the base report for the Virtual End Node (VEN).

    :raises Exception: If an error occurs during the registration process.
    """
    try:
      if not (self._vtn_name and self._ven_name):
        logger.warning('Cannot register base report: VTN or VEN name missing')
        return

      logger.info('Registering base report')
      self._ven.register_base_report()
    except Exception as e:
      logger.error(f'Failed to register base report: {e}')
      raise

  def add_task(self, task: Callable) -> None:
    """
    Add a task to the event loop.

    :param task: The task to add.
    :type task: Callable
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

    :param list_of_reports: List of report configurations.
    :type list_of_reports: Optional[List[ReportConfiguration]]
    """
    try:
      self._ven.add_reports(list_of_reports)
    except Exception as e:
      logger.error(f'Error adding report: {e}')

  def publish(self, signal: str, data: Any) -> None:
    """
    Publish a signal to subscribers.

    :param signal: The signal name.
    :type signal: str
    :param data: The data associated with the signal.
    :type data: Any
    """
    if signal in self._subscribers:
      for callback in self._subscribers[signal]:
        callback(data)
    logger.info(f'Published signal: {signal} with data: {data}')

  def subscribe(self, signal: str, callback: Callable) -> None:
    """
    Subscribe to a signal.

    :param signal: The signal name.
    :type signal: str
    :param callback: The callback function to call when the signal is received.
    :type callback: Callable
    """
    if not callable(callback):
      raise TypeError('callback must be callable')
    if signal not in self._subscribers:
      self._subscribers[signal] = []
    self._subscribers[signal].append(callback)
    logger.info(f'Subscribed to signal: {signal} with callback: {callback.__name__}')
