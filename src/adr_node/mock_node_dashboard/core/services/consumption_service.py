# src/core/services/consumption_service_impl.py
from typing import Optional
import threading
import requests
import logging
import time

from src.adr_node.mock_node_dashboard.core.domains.consumption_data import (
  ConsumptionData,
)
from src.adr_node.mock_node_dashboard.core.interfaces.iconsumption_service import (
  IConsumptionService,
)


class ConsumptionService(IConsumptionService):
  def __init__(self, base_url: str, update_interval: int = 5):
    self.base_url = base_url
    self.update_interval = update_interval
    self._last_consumption = 0.0
    self._lock = threading.Lock()
    self._running = False
    self._update_thread = None
    self.logger = logging.getLogger(__name__)

  def start(self) -> None:
    """Start the background update thread"""
    if not self._running:
      self._running = True
      self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
      self._update_thread.start()

  def stop(self) -> None:
    """Stop the background update thread"""
    self._running = False
    if self._update_thread:
      self._update_thread.join()

  def _update_loop(self) -> None:
    """Background loop to update consumption data"""
    while self._running:
      try:
        data = self.get_consumption_summary()
        if data:
          pass
          # UPDATE CONSself.event_bus.publish("consumption_updated", data)
      except Exception as e:
        self.logger.error(f'Error in update loop: {e}')
      time.sleep(self.update_interval)

  def get_consumption_summary(self) -> Optional[ConsumptionData]:
    try:
      response = requests.get(f'{self.base_url}/api/consumption/summary')
      response.raise_for_status()
      data = response.json()

      with self._lock:
        self._last_consumption = data['total_consumption']

      return ConsumptionData.from_dict(data)
    except Exception as e:
      self.logger.error(f'Failed to fetch consumption data: {e}')
      return None

  def get_current_consumption(self) -> float:
    with self._lock:
      return self._last_consumption
