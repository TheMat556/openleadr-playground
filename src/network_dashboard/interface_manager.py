import asyncio
from pathlib import Path

import gradio as gr
from typing import List, TYPE_CHECKING, Optional

import logging

from .helper import constants
from .helper.config import ContainerConfig
from .hierarchy_plot_manager import HierarchyPlotManager

if TYPE_CHECKING:
  from .dashboard import NetworkDashboard


class InterfaceManager:
  """
  Manages the creation and updating of the Gradio interface for the dashboard.

  Attributes
  ----------
  dashboard : NetworkDashboard
      The dashboard instance containing configurations and state.
  _plot_components : dict
      Dictionary of plot components indexed by container name.
  """

  def __init__(self, dashboard: 'NetworkDashboard'):
    """
    Initializes the InterfaceManager with a dashboard instance.

    Parameters
    ----------
    dashboard : NetworkDashboard
        The dashboard instance containing configurations and state.
    """
    self.dashboard = dashboard
    self.hierarchy_plot_manager = HierarchyPlotManager(dashboard.configs)
    self._plot_components = {'hierarchy': gr.Plot(visible=False)}

  def create_interface(self) -> gr.Blocks:
    """
    Creates the Gradio interface for the dashboard.

    This method sets up the Gradio interface, including the layout,
    sidebar, and main content area. It also handles the timers for updating
    load profile and consumption data asynchronously.

    Returns
    -------
    gr.Blocks
        Gradio interface blocks.
    """
    css = self._get_css_styles()
    with gr.Blocks(css=css) as interface:
      self.dashboard.add_all_to_state()
      state_var = gr.State(self.dashboard.state)

      self._create_layout(state_var)
      self._setup_update_callbacks(state_var)

      interface.load(
        self._update_plots,
        inputs=[state_var],
        outputs=list(self._plot_components.values()),
      )
      state_var.change(
        self._update_plots,
        inputs=[state_var],
        outputs=list(self._plot_components.values()),
      )

      return interface

  @staticmethod
  def _get_css_styles() -> str:
    """
    Returns CSS styles for the Gradio interface.

    Returns
    -------
    str
        CSS styles for the dashboard layout.
    """
    css_path = Path('./src/network_dashboard/styles.css').resolve()
    css_path_parts = css_path.parts
    if 'development' in css_path_parts:
      css_path_parts = tuple(part for part in css_path_parts if part != 'development')
      css_path = Path(*css_path_parts)
    return css_path.read_text()

  def _create_layout(self, state_var: gr.State) -> None:
    """
    Creates the layout for the Gradio interface.

    Parameters
    ----------
    state_var : gr.State
        State variable for the Gradio interface.
    """
    with gr.Row(elem_id='dashboard-layout'):
      self._create_sidebar(state_var)
      self._create_main_content()

  def _create_sidebar(self, state_var: gr.State) -> None:
    """
    Creates the sidebar for the Gradio interface.

    Parameters
    ----------
    state_var : gr.State
        State variable for the Gradio interface.
    """
    with gr.Column(elem_id='sidebar', scale=1):
      self._create_visualize_button(state_var)  # Moved above the accordion
      with gr.Accordion('Layers', open=True):
        self._create_overview_buttons(state_var)
        self._create_layer_buttons(state_var)

  def _create_overview_buttons(self, state_var: gr.State) -> None:
    """
    Creates overview buttons for the sidebar.

    Parameters
    ----------
    state_var : gr.State
        State variable for the Gradio interface.
    """
    gr.Button('General Overview').click(
      lambda: self.dashboard.add_all_to_state() or self.dashboard.state,
      inputs=None,
      outputs=state_var,
    )

    for layer in self.dashboard.get_unique_layers():
      gr.Button(f'Layer {layer} Overview').click(
        lambda layer_num=layer: self.dashboard.add_layer_to_state(layer_num)
        or self.dashboard.state,
        inputs=None,
        outputs=state_var,
      )

  def _create_layer_buttons(self, state_var: gr.State) -> None:
    """
    Creates buttons for each layer in the sidebar.

    Parameters
    ----------
    state_var : gr.State
        State variable for the Gradio interface.
    """
    max_layer = max(config.layer for config in self.dashboard.configs)
    for layer in range(max_layer + 1):
      with gr.Accordion(f'Layer {layer}', open=False):
        self._create_buttons_for_layer(layer, state_var)

  def _create_buttons_for_layer(self, layer: int, state_var: gr.State) -> None:
    """
    Creates buttons for a specific layer in the sidebar.

    Parameters
    ----------
    layer : int
        The layer number.
    state_var : gr.State
        State variable for the Gradio interface.
    """
    for config in self.dashboard.configs:
      if config.layer == layer:
        gr.Button(f'{config.container_name} {config.rest_api_port}').click(
          lambda c=config: self.dashboard.set_state_to_single_config(c)
          or self.dashboard.state,
          inputs=None,
          outputs=state_var,
        )

  @staticmethod
  def _create_visualize_button(state_var: gr.State) -> None:
    gr.Button('Visualize Hierarchy').click(
      lambda: 'hierarchy',
      inputs=None,
      outputs=state_var,
    )

  def _create_main_content(self) -> None:
    """
    Creates the main content area with plot components.
    """
    with gr.Column(elem_id='main-content', scale=4):
      with gr.Blocks(elem_classes='plot-grid'):
        for config in self.dashboard.configs:
          plot = gr.Plot(visible=False)
          self._plot_components[config.container_name] = plot

        self._plot_components['hierarchy'].render()

  def _setup_update_callbacks(self, state_var: gr.State) -> None:
    """
    Sets up update callbacks for load profile and consumption data.
    """

    async def combined_update():
      """Combines both data updates into a single async function."""
      await asyncio.gather(
        self.dashboard.data_manager.update_load_profile_data(),
        self.dashboard.data_manager.update_consumption_data(),
      )
      return None

    timer = gr.Timer(constants.LOAD_PROFILE_UPDATE_INTERVAL)

    timer.tick(combined_update, inputs=[], outputs=[])
    timer.tick(
      self._update_plots,
      inputs=[state_var],
      outputs=list(self._plot_components.values()),
    )

  def _update_plots(self, state: List[ContainerConfig]) -> List[gr.Plot]:
    """
    Updates plot components based on the current state.

    Parameters
    ----------
    state : List[ContainerConfig]
        Current state of the dashboard.

    Returns
    -------
    List[gr.Plot]
        Updated list of plot components.
    """
    outputs = [gr.Plot(visible=False) for _ in self._plot_components.values()]

    if isinstance(state, str) and state == 'hierarchy':
      try:
        hierarchy_plot = self.hierarchy_plot_manager.visualize_hierarchy()
        outputs[-1] = gr.Plot(value=hierarchy_plot, visible=True)
      except Exception as e:
        logging.error(f'Failed to create hierarchy visualization: {e}')
        outputs[-1] = gr.Plot(visible=False)
    else:
      for idx, config in enumerate(state):
        buffer = self.dashboard.data_manager.data_buffers.get(
          config.container_name, {'consumption': [], 'load_profile': []}
        )
        plot = self.dashboard.plot_manager.create_combined_plot(buffer, config)
        outputs[idx] = gr.Plot(value=plot, visible=True)

    return outputs

  def _get_parent_name(self, connect_vtn_url: str) -> Optional[str]:
    if not connect_vtn_url:
      logging.warning('connect_vtn_url is None or empty')
      return None

    for config in self.dashboard.configs:
      if config.VTN_URL == connect_vtn_url:
        return config.container_name

    logging.warning(f'No matching parent config found for URL: {connect_vtn_url}')
    return None
