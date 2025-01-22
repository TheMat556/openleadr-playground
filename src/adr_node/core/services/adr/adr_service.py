import asyncio
from typing import Optional, Callable, Dict, List

from src.adr_node.config.adr_config import AdrConfig
from src.adr_node.core.nodes.interfaces.ivirtual_end_node import IVirtualEndNode
from src.adr_node.core.nodes.interfaces.ivirtual_top_node import IVirtualTopNode
from src.adr_node.core.services.adr.interfaces.iadr_service import IAdrService
from src.openadr_node import logger
from src.openadr_node.models import ReportConfiguration
from src.adr_node.core.nodes.virtual_end_node import VirtualEndNode
from src.adr_node.core.nodes.virtual_top_node import VirtualTopNode


class AdrService(IAdrService):
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

  @property
  def vtn(self) -> Optional[VirtualTopNode]:
    return self._vtn

  @property
  def ven(self) -> Optional[VirtualEndNode]:
    return self._ven

  def create_node_tasks(self) -> None:
    if self._vtn:
      task = self._loop.create_task(
        self._vtn.run(),
      )
      self._tasks.append(task)
      self._loop.run_forever()

    if self._ven:
      self._register_base_report()
      task = self._loop.create_task(
        self._ven.run(),
      )
      self._tasks.append(task)

  def run(self):
    self._loop.run_forever()

  def shutdown(self) -> None:
    logger.info('Initiating shutdown of OpenADR controller...')
    for task in self._tasks:
      logger.debug(f'Cancelling task: {task.get_name()}')
      task.cancel()
    self._loop.run_until_complete(asyncio.gather(*self._tasks, return_exceptions=True))
    logger.info('OpenADR controller shutdown completed')

  def _register_base_report(self) -> None:
    try:
      if not (self._vtn_name and self._ven_name):
        logger.warning('Cannot register base report: VTN or VEN name missing')
        return
      logger.info('Registering base report')
      self._ven.register_base_report()
    except Exception as e:
      logger.error(f'Failed to register base report: {e}')
      raise

  def add_reports(
    self, list_of_reports: Optional[List[ReportConfiguration]] = None
  ) -> None:
    print('list_of_reports', list_of_reports)
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
