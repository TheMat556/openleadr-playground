import asyncio
import multiprocessing
import os
import threading
from random import random
from typing import Optional, List, Any, Dict
from datetime import datetime, timezone, timedelta

from src.openadr_node.models import ReportConfiguration, EventSignal, Interval
from src.openadr_node.virtual_end_node import VirtualEndNode
from src.openadr_node.virtual_top_node import VirtualTopNode

from pydispatch import dispatcher


class NodeManager:
  def __init__(
    self,
    vtn_name: Optional[str] = None,
    ven_name: Optional[str] = None,
    vtn_url: Optional[str] = None,
  ):
    self._vtn_name: Optional[str] = vtn_name
    self._ven_name: Optional[str] = ven_name
    self._vtn_url: Optional[str] = vtn_url

    self._loop = asyncio.get_event_loop()
    self._create_node_tasks()
    self._topics: Dict[str, Any] = {}

    print(dispatcher)
    dispatcher.connect(self._update_load_profile, signal='update_load_profile')

  def event_response_callback(self):
    print("callback done")

  def _update_load_profile(self, sender, data):
    self._topics['load_profile'] = data
    # event = EventSignal(
    #   ven_id=os.getenv('VEN_NAME'),
    #   signal_name='simple',
    #   signal_type='level',
    #   intervals=[{'dtstart': datetime(2021, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    #               'duration': timedelta(minutes=10),
    #               'signal_payload': 1}],
    #   callback=self.event_response_callback)
    print(f'LOADPROFILE has been updated from {sender}')
    self._dispatch_adr_event()

  def _create_node_tasks(self):
    if self._vtn_name:
      self._vtn = VirtualTopNode(self._vtn_name)
      self._loop.create_task(self._vtn.get_open_adr_server_run())

    if self._ven_name and self._vtn_url:
      self._ven = VirtualEndNode(self._ven_name, self._vtn_url, self._update_manager)
      self._loop.create_task(self._ven.get_open_adr_server_run())

  def _dispatch_adr_event(self):
    """Dispatch ADR event when load profile is updated."""
    print('Dispatching ADR event')
    event = EventSignal(
      ven_id='ven_123',
      signal_name='simple',
      signal_type='level',
      intervals=[
        Interval(
          dtstart=datetime(2021, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
          duration=timedelta(minutes=10),
          signal_payload=1,
        )
      ],
      callback=self._event_response_callback,
    )
    self._vtn.dispatch_adr_event(event)

  @staticmethod
  async def _event_response_callback(self, ven_id, event_id, opt_type) -> None:
    print(f'The VEN decided to {opt_type}')

  def add_task(self, task):
    """Add a task to the event loop."""
    print('!!!')
    self._loop.create_task(task())
    print('!!!')

    # process = multiprocessing.Process(target=task, args=([self._queue]))
    # process.start()

  def run_node(self):
    """Run the event loop."""
    self._loop.run_forever()

  def _update_manager(self, data: Any):
    """Update manager with received data."""
    print(data)

  def add_report(self, list_of_reports: Optional[List[ReportConfiguration]] = None):
    """Add reports to the VEN."""
    self._ven.add_reports(list_of_reports)
