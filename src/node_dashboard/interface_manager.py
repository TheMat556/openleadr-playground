import asyncio
from pathlib import Path

import gradio as gr
from typing import List, TYPE_CHECKING

from .helper import constants
from .helper.config import ContainerConfig

if TYPE_CHECKING:
  from .dashboard import GradioNodeDashboard


class InterfaceManager:
  """
  Manages the creation and updating of the Gradio interface for the dashboard.

  Attributes
  ----------
  dashboard : GradioNodeDashboard
      The dashboard instance containing configurations and state.
  _plot_components : dict
      Dictionary of plot components indexed by container name.
  plot_components : list
      List of plot components in the Gradio interface.
  """

  def __init__(self, dashboard: 'GradioNodeDashboard'):
    """
    Initializes the InterfaceManager with a dashboard instance.

    Parameters
    ----------
    dashboard : GradioNodeDashboard
        The dashboard instance containing configurations and state.
    """
    self.dashboard = dashboard
    self._plot_components = {}  # Dictionary for easy lookup
    self.plot_components = []  # List for Gradio compatibility

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
        self._update_plots, inputs=[state_var], outputs=self.plot_components
      )
      state_var.change(
        self._update_plots, inputs=[state_var], outputs=self.plot_components
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
    css_path = Path('./src/node_dashboard/styles.css').resolve()
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
        for config in self.dashboard.configs:
          if config.layer == layer:
            gr.Button(f'{config.container_name} {config.rest_api_port}').click(
              lambda c=config: self.dashboard.set_state_to_single_config(c)
              or self.dashboard.state,
              inputs=None,
              outputs=state_var,
            )

  def _create_main_content(self) -> None:
    """
    Creates the main content area with plot components.
    """
    with gr.Column(elem_id='main-content', scale=4):
      with gr.Blocks(elem_classes='plot-grid'):
        # Create all plot components up front
        for config in self.dashboard.configs:
          plot = gr.Plot(visible=False)
          self._plot_components[config.container_name] = plot
          self.plot_components.append(plot)

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
      return None  # For Gradio compatibility

    timer_load_profile = gr.Timer(constants.LOAD_PROFILE_UPDATE_INTERVAL)
    timer_consumption_data = gr.Timer(constants.CONSUMPTION_UPDATE_INTERVAL)

    # Set up timer callbacks
    timer_load_profile.tick(combined_update, inputs=[], outputs=[])
    timer_consumption_data.tick(combined_update, inputs=[], outputs=[])
    timer_load_profile.tick(
      self._update_plots, inputs=[state_var], outputs=self.plot_components
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
    outputs = [gr.Plot(visible=False) for _ in self.plot_components]

    if not state:
      return outputs

    for idx, config in enumerate(state):
      buffer = self.dashboard.data_manager.data_buffers.get(
        config.container_name, {'consumption': [], 'load_profile': []}
      )
      plot = self.dashboard.plot_manager.create_combined_plot(buffer, config)
      outputs[idx] = gr.Plot(value=plot, visible=True)

    return outputs
