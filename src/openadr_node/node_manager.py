import asyncio
import os
from typing import Optional, List, Any, Dict
from datetime import datetime, timezone, timedelta

from src.openadr_node import logger
from src.openadr_node.adr_base_config import AdrBaseConfig
from src.openadr_node.models import ReportConfiguration, EventSignal
from src.openadr_node.virtual_end_node import VirtualEndNode
from src.openadr_node.virtual_top_node import VirtualTopNode

from pydispatch import dispatcher


class NodeManager(AdrBaseConfig):
  def __init__(
    self,
    vtn_name: Optional[str] = None,
    ven_name: Optional[str] = None,
    vtn_url: Optional[str] = None,
  ):
    super().__init__()
    self._vtn_name: Optional[str] = vtn_name
    self._ven_name: Optional[str] = ven_name
    self._vtn_url: Optional[str] = vtn_url

    self._loop = asyncio.get_event_loop()
    self._create_node_tasks()
    self._topics: Dict[str, Any] = {}

    dispatcher.send(signal='on_ready', sender='system')

  def _register_dispatcher(self, sender, signal, data):
    method_name = '_on_' + data
    method = getattr(self, method_name, None)
    if callable(method):
      # If we have a method here custom sending have to be implemented
      dispatcher.connect(method, signal=data, sender=dispatcher.Any)
    else:
      dispatcher.connect(self._forward_dispatcher, signal=data, sender=sender)

    logger.info(f'NM - Connected {method_name} to signal: {data} with sender: {sender}')

  @staticmethod
  def _forward_dispatcher(sender, signal, data):
    return dispatcher.send(signal=signal, sender='nm', data=data)

  def event_response_callback(self):
    pass

  def _update_load_profile(self, sender, data):
    self._topics['load_profile'] = data
    event = EventSignal(
      ven_id=os.getenv('VEN_NAME'),
      signal_name='simple',
      signal_type='level',
      intervals=[
        {
          'dtstart': datetime(2021, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
          'duration': timedelta(minutes=10),
          'signal_payload': 1,
        }
      ],
      callback=None,
    )
    print(f'LOADPROFILE has been updated from {sender}')
    dispatcher.send(sender='nm', signal='update_load_profile', data=event)

  def _create_node_tasks(self):
    if self._vtn_name:
      self._vtn = VirtualTopNode(self._vtn_name)
      self._loop.create_task(self._vtn.get_open_adr_server_run())

    if self._ven_name and self._vtn_url:
      self._ven = VirtualEndNode(self._ven_name, self._vtn_url)
      self._loop.create_task(self._ven.get_open_adr_server_run())

  @staticmethod
  async def _event_response_callback(self, ven_id, event_id, opt_type) -> None:
    print(f'The VEN decided to {opt_type}')

  def add_task(self, task):
    self._loop.create_task(task())

  def run_node(self):
    self._loop.run_forever()

  def add_report(self, list_of_reports: Optional[List[ReportConfiguration]] = None):
    self._ven.add_reports(list_of_reports)
