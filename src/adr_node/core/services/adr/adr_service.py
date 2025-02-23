import asyncio
import time
from typing import Optional, Callable, Dict, List

from src.adr_node.config.adr_config import AdrConfig
from src.adr_node.core.nodes.domains.report_configuration import ReportConfiguration
from src.adr_node.core.nodes.implementation.virtual_end_node import VirtualEndNode
from src.adr_node.core.nodes.implementation.virtual_top_node import VirtualTopNode
from src.adr_node.core.nodes.interfaces.ivirtual_end_node import IVirtualEndNode
from src.adr_node.core.nodes.interfaces.ivirtual_top_node import IVirtualTopNode
from src.adr_node.core.services.adr.interfaces.iadr_service import IAdrService
import logging


class AdrService(IAdrService):
  """
  ADR Service implementation for the OpenADR system.

  This class provides methods to manage the ADR service, including
  creating node tasks, running the service, shutting it down, and
  handling reports.

  Attributes
  ----------
  _vtn_name : str
      The name of the VTN.
  _ven_name : str
      The name of the VEN.
  _vtn_url : str
      The URL of the VTN.
  _openadr_http_host : str
      The HTTP host for OpenADR.
  _openadr_http_port : int
      The HTTP port for OpenADR.
  _openadr_vtn_path_prefix : str
      The path prefix for the VTN.
  _vtn : Optional[IVirtualTopNode]
      The virtual top node.
  _ven : Optional[IVirtualEndNode]
      The virtual end node.
  _subscribers : Dict[str, List[Callable]]
      The subscribers for the ADR service.
  _report_queue : asyncio.Queue
      The queue for reports.
  _tasks : List[asyncio.Task]
      The tasks for the ADR service.
  _loop : asyncio.AbstractEventLoop
      The event loop for the ADR service.
  """

  def __init__(
    self,
    adr_config: AdrConfig,
    virtual_end_node: Optional[IVirtualEndNode] = None,
    virtual_top_node: Optional[IVirtualTopNode] = None,
  ):
    if isinstance(adr_config, dict):
      adr_config = AdrConfig(**adr_config)

    self._vtn_name = adr_config.vtn_name
    self._ven_name = adr_config.ven_name
    self._vtn_url = adr_config.vtn_url
    self._openadr_http_host = adr_config.openadr_http_host
    self._openadr_http_port = adr_config.openadr_http_port
    self._openadr_vtn_path_prefix = adr_config.openadr_vtn_path_prefix
    self._vtn = virtual_top_node
    self._ven = virtual_end_node
    self._subscribers: Dict[str, List[Callable]] = {}
    self._report_queue = asyncio.Queue()
    self._tasks = []

    try:
      self._loop = asyncio.get_running_loop()
    except RuntimeError:
      self._loop = asyncio.new_event_loop()
      asyncio.set_event_loop(self._loop)

    self.create_node_tasks()

  @property
  def vtn(self) -> Optional[VirtualTopNode]:
    """
    Get the virtual top node.

    Returns
    -------
    Optional[VirtualTopNode]
        The virtual top node.
    """
    return self._vtn

  @property
  def ven(self) -> Optional[VirtualEndNode]:
    """
    Get the virtual end node.

    Returns
    -------
    Optional[VirtualEndNode]
        The virtual end node.
    """
    return self._ven

  def create_node_tasks(self) -> None:
    """
    Create tasks for the ADR node.
    """
    if self._vtn:
      task = self._loop.create_task(
        self._vtn.run(),
      )
      self._tasks.append(task)

    if self._ven:
      time.sleep(5)
      self._register_base_reports()
      task = self._loop.create_task(
        self._ven.run(),
      )
      self._tasks.append(task)

  def run(self) -> None:
    """
    Run the ADR service.
    """
    self._loop.run_forever()

  def shutdown(self) -> None:
    """
    Shutdown the ADR service.
    """
    logging.info('Initiating shutdown of OpenADR controller...')
    for task in self._tasks:
      logging.debug(f'Cancelling task: {task.get_name()}')
      task.cancel()
    self._loop.run_until_complete(asyncio.gather(*self._tasks, return_exceptions=True))
    logging.info('OpenADR controller shutdown completed')

  def _register_base_reports(self) -> None:
    """
    Register the base report for the VEN.
    """
    try:
      if not self._ven:
        logging.warning('Cannot register base report: VEN is not defined')
        return
      logging.info('Registering base report')
      self._ven.register_base_report()
      self._ven.register_h_load_report()
    except Exception as e:
      logging.error(f'Failed to register base report: {e}')
      raise

  def add_reports(
    self, list_of_reports: Optional[List[ReportConfiguration]] = None
  ) -> None:
    """
    Add reports to the ADR service.

    Parameters
    ----------
    list_of_reports : Optional[List[ReportConfiguration]]
        List of report configurations to add.
    """
    try:
      if self._ven:
        self._ven.add_reports(list_of_reports)
      else:
        self._report_queue.put_nowait(list_of_reports)
        logging.info('Reports queued until VEN is available')
    except Exception as e:
      logging.error(f'Error adding report: {e}')

  async def _process_report_queue(self) -> None:
    """
    Process the queued reports when the VEN is available.
    """
    try:
      while not self._report_queue.empty():
        reports = await self._report_queue.get()
        self._ven.add_reports(reports)
        logging.info('Queued reports added to VEN')
    except Exception as e:
      logging.error(f'Error processing report queue: {e}')
