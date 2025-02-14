import asyncio
from typing import Dict
import gradio as gr
import logging

from src.network_dashobard.helper.constants import UPDATE_INTERVAL
from src.network_dashobard.interfaces.idata_manager import IDataManager
from src.network_dashobard.interfaces.iplot_manager import IPlotManager
from src.network_dashobard.services.services import IUpdateService


class UpdateService(IUpdateService):
  def __init__(
    self,
    data_manager: IDataManager,
    plot_manager: IPlotManager,
    update_interval: float = UPDATE_INTERVAL,
  ):
    self.data_manager = data_manager
    self.plot_manager = plot_manager
    self.update_interval = update_interval
    self._update_task = None

  def setup_callbacks(self, plot_components: Dict[str, gr.Plot]) -> None:
    """Sets up update callbacks for the interface"""

    async def update_data():
      """Updates both load profile and consumption data"""
      try:
        await asyncio.gather(
          self.data_manager.update_load_profile_data(),
          self.data_manager.update_consumption_data(),
        )
      except Exception as e:
        logging.error(f'Error updating data: {e}')

    # Create update timer
    timer = gr.Timer(self.update_interval)
    timer.tick(update_data)

    # Setup auto-refresh toggle
    def toggle_updates(enabled: bool):
      if enabled and not self._update_task:
        self._update_task = asyncio.create_task(self._continuous_update())
      elif not enabled and self._update_task:
        self._update_task.cancel()
        self._update_task = None

    return toggle_updates

  async def _continuous_update(self):
    """Continuously updates data at specified interval"""
    while True:
      try:
        await asyncio.gather(
          self.data_manager.update_load_profile_data(),
          self.data_manager.update_consumption_data(),
        )
        await asyncio.sleep(self.update_interval)
      except asyncio.CancelledError:
        break
      except Exception as e:
        logging.error(f'Error in continuous update: {e}')
        await asyncio.sleep(self.update_interval)
