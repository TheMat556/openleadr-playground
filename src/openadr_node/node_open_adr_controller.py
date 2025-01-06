import asyncio
from typing import Optional, Callable, Dict, List, Any
from src.openadr_node import logger
from src.openadr_node.models import ReportConfiguration
from src.openadr_node.virtual_end_node import VirtualEndNode
from src.openadr_node.virtual_top_node import VirtualTopNode


class NodeOpenADRController:
  """
  Controller for managing OpenADR node tasks, including VTN and VEN operations.

  Attributes
  ----------
  loop : asyncio.AbstractEventLoop
      Event loop for running asynchronous tasks.
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
  vtn : Optional[VirtualTopNode]
      Instance of the Virtual Top Node.
  ven : Optional[VirtualEndNode]
      Instance of the Virtual End Node.
  subscribers : Dict[str, List[Callable]]
      Dictionary to store subscribers for signals.
   _report_queue : Queue
        Queue to store reports until the VEN is available.
  """

  def __init__(
    self,
    loop: asyncio.AbstractEventLoop,
    vtn_name: Optional[str] = None,
    ven_name: Optional[str] = None,
    vtn_url: Optional[str] = None,
    openadr_http_host: Optional[str] = None,
    openadr_http_port: Optional[int] = None,
    openadr_vtn_path_prefix: Optional[str] = None,
  ):
    """
    Initialize the NodeOpenADRController with the given parameters.
    """
    self._loop = loop
    self._vtn_name = vtn_name
    self._ven_name = ven_name
    self._vtn_url = vtn_url
    self._openadr_http_host = openadr_http_host
    self._openadr_http_port = openadr_http_port
    self._openadr_vtn_path_prefix = openadr_vtn_path_prefix
    self._vtn = None
    self._ven = None
    self._subscribers: Dict[str, List[Callable]] = {}
    self._report_queue = asyncio.Queue()
    self._tasks = []

  @property
  def vtn(self) -> Optional[VirtualTopNode]:
    return self._vtn

  @property
  def ven(self) -> Optional[VirtualEndNode]:
    return self._ven

  def create_node_tasks(self) -> None:
    """
    Create and start tasks for the VTN and VEN nodes.
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
        http_host=self._openadr_http_host,
        http_port=self._openadr_http_port,
        path_prefix=self._openadr_vtn_path_prefix,
      )
      task = self._loop.create_task(
        run_with_notification(
          self._vtn.get_open_adr_server_run(),
          start_callback=lambda: logger.info('VTN task started'),
          end_callback=lambda: self.publish('vtn_created', {'status': 'created'}),
        )
      )
      self._tasks.append(task)

    if self._ven_name and self._vtn_url:
      self._ven = VirtualEndNode(self._ven_name, self._vtn_url)
      self._register_base_report()
      task = self._loop.create_task(
        run_with_notification(
          self._ven.get_open_adr_server_run(),
          start_callback=lambda: logger.info('VEN task started'),
          end_callback=lambda: self.publish('ven_ready', {'status': 'ready'}),
        )
      )
      self._tasks.append(task)

  def shutdown(self) -> None:
    for task in self._tasks:
      task.cancel()
    self._loop.run_until_complete(asyncio.gather(*self._tasks, return_exceptions=True))

  def _register_base_report(self) -> None:
    """
    Register the base report for the VEN.
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
      if self._ven:
        self._ven.add_reports(list_of_reports)
      else:
        self._report_queue.put_nowait(list_of_reports)
        logger.info('Reports queued until VEN is available')
    except Exception as e:
      logger.error(f'Error adding report: {e}')

  async def _process_report_queue(self) -> None:
    """
    Process the queued reports when the VEN is available.
    """
    try:
      while not self._report_queue.empty():
        reports = await self._report_queue.get()
        self._ven.add_reports(reports)
        logger.info('Queued reports added to VEN')
    except Exception as e:
      logger.error(f'Error processing report queue: {e}')

  def publish(self, signal: str, data: Any) -> None:
    """
    Publish a signal to subscribers.
    """
    if signal in self._subscribers:
      for callback in self._subscribers[signal]:
        callback(data)
    logger.info(f'Published signal: {signal} with data: {data}')

  def subscribe(self, signal: str, callback: Callable) -> None:
    """
    Subscribe to a signal.

    Parameters
    ----------
    signal : str
        The signal name.
    callback : Callable
        The callback function to call when the signal is received.
    """
    if not callable(callback):
      raise TypeError('callback must be callable')
    if signal not in self._subscribers:
      self._subscribers[signal] = []
    self._subscribers[signal].append(callback)
    logger.info(f'Subscribed to signal: {signal} with callback: {callback.__name__}')
