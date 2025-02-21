from datetime import datetime, timezone

from src.adr_node.core.interfaces.irunable import IRunnable
from src.adr_node.database.interfaces.services.iconsumption_service import (
  IConsumptionService,
)
from src.adr_node.database.interfaces.services.iloadprofile_service import (
  ILoadProfileService,
)
from src.adr_node.mock_node_dashboard.core.interfaces.islider_service import (
  ISliderService,
)
from src.adr_node.mock_node_dashboard.ui.components.chart import ChartComponent
from src.adr_node.mock_node_dashboard.ui.components.slider_grid import SliderGrid

import gradio as gr
import threading
from typing import List, Dict, Any
import logging
import queue


class EnergyControlPanel(IRunnable):
  """
  Energy Control Panel class to manage and display energy consumption and allowed consumption.

  :param consumption_service: Service to get consumption data.
  :type consumption_service: IConsumptionService
  :param loadprofile_service: Service to manage load profiles.
  :type loadprofile_service: ILoadProfileService
  :param slider_service: Service to manage slider values.
  :type slider_service: ISliderService
  :param num_sliders: Number of sliders in the grid.
  :type num_sliders: int
  :param max_slider_value: Maximum value for sliders.
  :type max_slider_value: int
  :param update_interval: Interval in seconds to update the interface.
  :type update_interval: int
  """

  def __init__(
    self,
    consumption_service: IConsumptionService,
    loadprofile_service: ILoadProfileService,
    slider_service: ISliderService,
    num_sliders: int = 24,
    max_slider_value: int = 30,
    update_interval: int = 5,
  ):
    self.consumption_service = consumption_service
    self.loadprofile_service = loadprofile_service
    self.slider_service = slider_service
    self.num_sliders = num_sliders
    self.max_slider_value = max_slider_value
    self.update_interval = update_interval
    self.logger = logging.getLogger(__name__)

    self._stop_event = threading.Event()
    self._thread = None
    self.queue = queue.Queue()

    self.chart = ChartComponent()
    self.slider_grid = SliderGrid(num_sliders=num_sliders, max_value=max_slider_value)
    self.interface = self.create_interface()

  def update_chart(self, *slider_values: List[int]) -> gr.Plot:
    """
    Update the chart based on slider values.

    :param slider_values: List of slider values.
    :type slider_values: List[int]
    :return: Updated plot.
    :rtype: gr.Plot
    """
    try:
      values = list(slider_values)
      fig = self.chart.create_figure(values)
      return fig
    except Exception as e:
      self.logger.error(f'Error updating chart: {e}')
      return self.chart.create_figure([0] * self.num_sliders)

  def _process_consumption_points(self, points: List[Any]) -> Dict[str, Any]:
    """
    Process consumption points to calculate totals and organize data.

    :param points: List of ConsumptionData objects.
    :type points: List[Any]
    :return: Processed consumption data.
    :rtype: Dict[str, Any]
    """
    if not points:
      raise ValueError('No consumption points available')

    total_value = sum(point.value for point in points)

    ven_consumption = {}
    for point in points:
      if point.ven_id not in ven_consumption:
        ven_consumption[point.ven_id] = {'value': 0, 'points': []}
      ven_consumption[point.ven_id]['value'] += point.value
      ven_consumption[point.ven_id]['points'].append(
        {
          'timestamp': point.timestamp,
          'value': point.value,
          'resource_id': point.resource_id,
        }
      )

    return {
      'total_consumption': total_value,
      'ven_count': len(ven_consumption),
      'unit': 'kWh',
      'ven_details': ven_consumption,
    }

  def get_current_consumption(self) -> str:
    """
    Get the current consumption value.

    :return: Current consumption in kWh.
    :rtype: str
    """
    try:
      timestamp = int(datetime.now(timezone.utc).timestamp())
      result = self.consumption_service.get_closest_consumption_points(
        target_timestamp=timestamp
      )
      consumption_points = result.data['consumption_points']
      processed_data = self._process_consumption_points(consumption_points)[
        'total_consumption'
      ]
      return f'{processed_data:.2f} kWh'
    except Exception as e:
      self.logger.error(f'Error getting consumption: {e}')
      return 'N/A'

  def get_current_allowed_consumption(self) -> str:
    """
    Get the current allowed consumption value.

    :return: Current allowed consumption in kWh.
    :rtype: str
    """
    try:
      allowed = self.slider_service.get_current_allowed_consumption()
      return f'{allowed:.2f} kWh'
    except Exception as e:
      self.logger.error(f'Error getting allowed consumption: {e}')
      return 'N/A'

  def create_interface(self) -> gr.Blocks:
    """
    Create the Gradio interface for the energy control panel.

    :return: Gradio Blocks interface.
    :rtype: gr.Blocks
    """
    initial_values = self.slider_service.load_values()

    with gr.Blocks(css='.gradio-container { max-width: 95% !important; }') as interface:
      with gr.Column():
        slider_inputs = self.slider_grid.create()

        for slider, value in zip(slider_inputs, initial_values):
          slider.value = value

        plot_output = gr.Plot(
          value=lambda: self.chart.create_figure(initial_values),
          every=1,
        )

        for slider in slider_inputs:
          slider.change(fn=self.update_chart, inputs=slider_inputs, outputs=plot_output)
          slider.release(fn=self.slider_service.save_values, inputs=slider_inputs)

        with gr.Row():
          gr.Label(
            value=lambda: self.get_current_consumption(),
            label='Current Consumption',
            every=self.update_interval,
          )
          gr.Label(
            value=lambda: self.get_current_allowed_consumption(),
            label='Allowed Consumption',
            every=self.update_interval,
          )

    return interface

  def _run_server(self):
    """
    Run the Gradio server.
    """
    try:
      self.interface.launch(
        server_name='0.0.0.0',
        server_port=7862,
        show_api=False,
        share=False,
        prevent_thread_lock=True,
        quiet=True,
      )
    except Exception as e:
      self.logger.error(f'Error in Gradio server thread: {e}')
      self.queue.put(e)

  def run(self) -> None:
    """
    Start the energy control panel.
    """
    try:
      self.logger.info('Starting Threaded Energy Control Panel...')
      self._thread = threading.Thread(target=self._run_server)
      self._thread.daemon = True
      self._thread.start()

      while not self._stop_event.is_set():
        try:
          error = self.queue.get_nowait()
          if isinstance(error, Exception):
            raise error
        except queue.Empty:
          pass
        self._stop_event.wait(1)

    except Exception as e:
      self.logger.error(f'Failed to start: {e}')
      raise

  def stop(self) -> None:
    """
    Stop the energy control panel.
    """
    try:
      self._stop_event.set()
      if self._thread and self._thread.is_alive():
        self._thread.join(timeout=5)
      self.logger.info('Threaded Energy Control Panel stopped')
    except Exception as e:
      self.logger.error(f'Error stopping Threaded Energy Control Panel: {e}')
      raise
