# src/ui/app.py
import gradio as gr
from typing import List
import logging

from src.adr_node.mock_node_dashboard.core.interfaces.iconsumption_service import (
  IConsumptionService,
)
from src.adr_node.mock_node_dashboard.core.interfaces.islider_service import (
  ISliderService,
)
from src.adr_node.mock_node_dashboard.ui.components.chart import ChartComponent
from src.adr_node.mock_node_dashboard.ui.components.slider_grid import SliderGrid


class AsyncGradioApp:
  """
  Main Gradio application class that integrates all UI components and services.
  """

  def __init__(
    self,
    consumption_service: IConsumptionService,
    slider_service: ISliderService,
    num_sliders: int = 24,
    max_slider_value: int = 30,
    update_interval: int = 5,
  ):
    self.consumption_service = consumption_service
    self.slider_service = slider_service
    self.num_sliders = num_sliders
    self.max_slider_value = max_slider_value
    self.update_interval = update_interval
    self.logger = logging.getLogger(__name__)

    # Initialize UI components
    self.chart = ChartComponent()
    self.slider_grid = SliderGrid(num_sliders=num_sliders, max_value=max_slider_value)

  def update_chart(self, *slider_values: List[int]) -> gr.Plot:
    """
    Update the chart with new slider values.

    Args:
        *slider_values: Variable number of slider values

    Returns:
        Updated Plotly figure
    """
    try:
      values = list(slider_values)
      fig = self.chart.create_figure(values)
      return fig
    except Exception as e:
      self.logger.error(f'Error updating chart: {e}')
      return self.chart.create_figure([0] * self.num_sliders)

  def get_current_consumption(self) -> str:
    """
    Get formatted string of current consumption.

    Returns:
        Formatted consumption string
    """
    try:
      consumption = self.consumption_service.get_current_consumption()
      return f'{consumption:.2f} kWh'
    except Exception as e:
      self.logger.error(f'Error getting current consumption: {e}')
      return 'N/A'

  def get_current_allowed_consumption(self) -> str:
    """
    Get formatted string of current allowed consumption.

    Returns:
        Formatted allowed consumption string
    """
    try:
      allowed = self.slider_service.get_current_allowed_consumption()
      return f'{allowed:.2f} kWh'
    except Exception as e:
      self.logger.error(f'Error getting allowed consumption: {e}')
      return 'N/A'

  def create_interface(self) -> gr.Blocks:
    """
    Create the complete Gradio interface.

    Returns:
        Gradio Blocks interface
    """
    with gr.Blocks(css='.gradio-container { max-width: 95% !important; }') as interface:
      with gr.Column():
        # Create slider grid
        slider_inputs = self.slider_grid.create()

        # Create chart
        plot_output = gr.Plot()

        # Initial chart update
        initial_values = self.slider_service.load_values()
        self.slider_grid.set_values(initial_values)
        plot_output.value = self.chart.create_figure(initial_values)

        # Wire up events
        for slider in slider_inputs:
          print("slider", slider)
          slider.change(fn=self.tst, inputs=slider_inputs, outputs=plot_output)
          slider.release(fn=self.slider_service.save_values, inputs=slider_inputs)

        # Add consumption labels
        with gr.Row():
          gr.Label(
            value=self.get_current_consumption,
            label='Current Consumption',
            every=self.update_interval,
          )
          gr.Label(
            value=self.get_current_allowed_consumption,
            label='Allowed Consumption',
            every=self.update_interval,
          )

    return interface

  def tst(self, tst: any):
    print("!!! tst print", tst)
