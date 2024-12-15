import asyncio
import logging
import sys
from typing import Optional, List, Any, Dict, Callable

import pandas as pd
from flask import Flask, jsonify

from src.openadr_node import logger
from src.openadr_node.adr_base_config import AdrBaseConfig
from src.openadr_node.models import ReportConfiguration
from src.openadr_node.virtual_end_node import VirtualEndNode
from src.openadr_node.virtual_top_node import VirtualTopNode

from pydispatch import dispatcher
from threading import Thread


def rest_endpoint(path: str) -> Callable:
  def decorator(func: Callable) -> Callable:
    func._rest_endpoint = True
    func._rest_path = path
    return func

  return decorator


class NodeManager(AdrBaseConfig):
  def __init__(
    self,
    vtn_name: Optional[str] = None,
    ven_name: Optional[str] = None,
    vtn_url: Optional[str] = None,
    http_host: Optional[str] = None,
    http_port: Optional[int] = None,
    vtn_path_prefix: Optional[str] = None,
    rest_api_port: Optional[int] = None,
  ):
    super().__init__()
    self._vtn_name: Optional[str] = vtn_name
    self._vtn_url: Optional[str] = vtn_url
    self._ven_name: Optional[str] = ven_name
    self._http_host: Optional[str] = http_host
    self._http_port: Optional[int] = http_port
    self._vtn_path_prefix: Optional[str] = vtn_path_prefix
    self._rest_api_port: Optional[int] = rest_api_port

    self._loop = asyncio.get_event_loop()
    self._create_node_tasks()
    self._topics: Dict[str, Any] = {}
    self._subscribers: Dict[str, List[Callable]] = {}

    dispatcher.send(signal='on_ready', sender='system')

    self.app = Flask(__name__)
    self._init_routes()
    self._start_flask()

  def get_method(self, signal: str) -> Optional[Callable]:
    method_name = '_on_' + signal
    return getattr(self, method_name, None)

  def _register_dispatcher(self, sender: str, signal: str, data: str) -> None:
    method = self.get_method(data)
    if callable(method):
      dispatcher.connect(self._call_method, signal=data, sender=dispatcher.Any)
    else:
      dispatcher.connect(self._forward_dispatcher, signal=data, sender=sender)

    logger.info(
      f'NM - Connected {"_on" + signal} to signal: {data} with sender: {sender}'
    )

  @staticmethod
  def _forward_dispatcher(sender: str, signal: str, data: Any) -> None:
    dispatcher.send(signal=signal, sender='nm', data=data)

  def _call_method(self, sender: str, signal: str, data: Any) -> None:
    if sender == 'nm':
      return

    method = self.get_method(signal)
    if callable(method):
      try:
        method(sender, data)
      except Exception as e:
        logger.error(f'Error calling method {signal}: {e}')
        raise

  def event_response_callback(self) -> None:
    pass

  def _on_update_load_profile(self, sender: str, data: List[Dict[str, Any]]) -> None:
    print(f'LOADPROFILE has been updated from {sender}')

    if not isinstance(data, list):
      logger.error('Invalid data format: expected list of intervals')
      return

    transformed_data = [
      {
        'time': interval['dtstart'].strftime('%H:%M'),
        'value': interval['signal_payload'],
      }
      for interval in data
    ]
    df = pd.DataFrame(transformed_data)
    self._topics['load_profile'] = df
    df.set_index('time', inplace=True)

    dispatcher.send(sender='nm', signal='update_load_profile', data=data)

  def _create_node_tasks(self) -> None:
    async def run_with_notification(
      coro: Callable,
      start_callback: Optional[Callable],
      end_callback: Optional[Callable],
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
          start_callback=lambda: print('VTN task started'),
          end_callback=lambda: self.publish('vtn_created', {'status': 'created'}),
        )
      )

    if self._ven_name and self._vtn_url:
      print('VEN NAME:', self._ven_name)
      print('VTN URL:', self._vtn_url)
      self._ven = VirtualEndNode(self._ven_name, self._vtn_url)
      self._loop.create_task(
        run_with_notification(
          self._ven.get_open_adr_server_run(),
          start_callback=lambda: print('VEN task started'),
          end_callback=lambda: print('VEN task finished'),
        )
      )

  @staticmethod
  async def _event_response_callback(ven_id: str, event_id: str, opt_type: str) -> None:
    print(f'The VEN decided to {opt_type}')

  def add_task(self, task: Callable) -> None:
    self._loop.create_task(task())

  def run_node(self) -> None:
    self._loop.run_forever()

  def add_report(
    self, list_of_reports: Optional[List[ReportConfiguration]] = None
  ) -> None:
    self._ven.add_reports(list_of_reports)

  def _init_routes(self) -> None:
    for attr_name in dir(self):
      attr = getattr(self, attr_name)
      if callable(attr) and getattr(attr, '_rest_endpoint', False):
        self.app.add_url_rule(attr._rest_path, view_func=attr, methods=['GET'])

  def _start_flask(self) -> None:
    def run_flask() -> None:
      port = self._rest_api_port
      if self._rest_api_port is None:
        logging.info('REST API port not set, node manager executing will exit')
        sys.exit(1)
      try:
        self.app.run(host='0.0.0.0', port=port)
      except OSError as e:
        logger.error(f'Failed to start Flask server: {e}')
        raise

    thread = Thread(target=run_flask)
    thread.daemon = True
    thread.start()

  @rest_endpoint('/data/load_profile')
  def get_load_profile(self) -> Any:
    load_profile = self._topics.get('load_profile', None)
    if load_profile is None:
      return jsonify({'error': 'Load profile not found'}), 404
    try:
      return load_profile.to_json(), 200, {'Content-Type': 'application/json'}
    except Exception as e:
      logger.error(f'Failed to serialize load profile: {e}')
      return jsonify({'error': 'Failed to serialize data'}), 500

  def publish(self, signal: str, data: Any) -> None:
    if signal in self._subscribers:
      for callback in self._subscribers[signal]:
        callback(data)
    logger.info(f'Published signal: {signal} with data: {data}')

  def subscribe(self, signal: str, callback: Callable) -> None:
    if signal not in self._subscribers:
      self._subscribers[signal] = []
    self._subscribers[signal].append(callback)
    logger.info(f'Subscribed to signal: {signal} with callback: {callback.__name__}')
