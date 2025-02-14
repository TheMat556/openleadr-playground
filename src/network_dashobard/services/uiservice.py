from pathlib import Path
from typing import Dict, List
import gradio as gr
import logging

from src.network_dashobard.config.container_config import ContainerConfig
from src.network_dashobard.interfaces.iplot_manager import IPlotManager
from src.network_dashobard.services.services import IUIService


class UIService(IUIService):
  def __init__(self, plot_manager: IPlotManager):
    self.plot_manager = plot_manager
    self._css_cache = None

  def get_css_styles(self) -> str:
    """Gets CSS styles for the Gradio interface"""
    if self._css_cache is None:
      css_path = Path('./src/node_dashboard/styles.css').resolve()
      css_path_parts = css_path.parts
      if 'development' in css_path_parts:
        css_path_parts = tuple(part for part in css_path_parts if part != 'development')
        css_path = Path(*css_path_parts)
      self._css_cache = css_path.read_text()
    return self._css_cache

  def create_sidebar_components(self, plot_components: Dict[str, gr.Plot]) -> None:
    """Creates sidebar components"""
    with gr.Column(elem_id='sidebar-components'):
      with gr.Accordion('Controls', open=True):
        gr.Button('Refresh Data')
        gr.Button('Clear Plots')

      with gr.Accordion('Display Options', open=True):
        gr.Checkbox('Auto-refresh', value=True)
        gr.Slider(minimum=1, maximum=60, value=10, label='Update Interval (s)')

  def create_main_content(self, plot_components: Dict[str, gr.Plot]) -> None:
    """Creates main content area with plot components"""
    with gr.Column(elem_id='main-content'):
      with gr.Tabs():
        with gr.TabItem('Plots'):
          with gr.Row():
            for name, plot in plot_components.items():
              plot.render()
        with gr.TabItem('Settings'):
          gr.JSON(label='Plot Configuration')

  def update_plots(
    self, state: List[ContainerConfig], plot_components: Dict[str, gr.Plot]
  ) -> List[gr.Plot]:
    """Updates plot components based on state"""
    outputs = []
    try:
      for component_name in plot_components:
        if component_name == 'hierarchy':
          outputs.append(gr.Plot(visible=False))
          continue

        for config in state:
          if config.container_name == component_name:
            fig = self.plot_manager.create_combined_plot(
              {},  # Empty data to create initial plot
              config,
              clear_existing=True,
            )
            outputs.append(gr.Plot(value=fig, visible=True))
            break
        else:
          outputs.append(gr.Plot(visible=False))
    except Exception as e:
      logging.error(f'Error updating plots: {e}')
      outputs = [gr.Plot(visible=False) for _ in plot_components]

    return outputs
