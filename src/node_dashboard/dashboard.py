import os
import logging
import asyncio
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

import aiohttp
import plotly.graph_objs as go
import gradio as gr

from src.node_dashboard.config import load_configs, ContainerConfig
from src.node_dashboard.utils import fetch_data_async, round_to_nearest_minute

logger = logging.getLogger(__name__)


class GradioNodeDashboard:
  """
  A class to represent the Gradio Node Dashboard.

  Attributes
  ----------
  configs : List[ContainerConfig]
      List of container configurations.
  state : List[ContainerConfig]
      Current state of the dashboard.
  plot_cache : Dict[str, go.Layout]
      Cache for plot layouts.
  data_buffers : Dict[str, Dict[str, List[Dict[str, Any]]]]
      Buffers to store fetched data.
  max_buffer_size : int
      Maximum size of the data buffers.

  Methods
  -------
  __init__(file_path: str = "./env_variables.json") -> None:
      Initializes the dashboard with configurations.
  update_consumption_data() -> None:
      Fetches and updates consumption data.
  update_load_profile_data() -> None:
      Fetches and updates load profile data.
  parse_time_to_datetime(time_str: str) -> datetime:
      Parses time string to datetime object.
  create_combined_plot(data: Dict[str, List[Dict[str, Any]]], config: ContainerConfig) -> go.Figure:
      Creates a combined plot of load profile and consumption data.
  _create_new_plot_layout(config: ContainerConfig) -> go.Figure:
      Creates a new plot layout for a container.
  update_state(new_state: List[ContainerConfig]) -> None:
      Updates the current state.
  add_to_state(config: ContainerConfig) -> None:
      Adds a single configuration to the state.
  add_all_to_state() -> None:
      Adds all configurations to the state.
  add_layer_to_state(layer: int) -> None:
      Adds configurations of a specific layer to the state.
  get_unique_layers() -> List[int]:
      Gets a list of unique layers.
  create_interface() -> gr.Blocks:
      Creates the Gradio interface.
  _get_css_styles() -> str:
      Returns CSS styles for the interface.
  _create_layout(state_var: gr.State) -> None:
      Creates the layout for the dashboard.
  _create_sidebar(state_var: gr.State) -> None:
      Creates the sidebar for the dashboard.
  _create_layer_buttons(state_var: gr.State) -> None:
      Creates buttons for each layer in the sidebar.
  _create_main_content() -> None:
      Creates the main content area for the dashboard.
  _update_plot_components(state: List[ContainerConfig]) -> List[gr.Plot]:
      Updates the plot components.
  """

  def __init__(self, file_path: str = './env_variables.json') -> None:
    """
    Initializes the GradioNodeDashboard with configurations.

    Parameters
    ----------
    file_path : str, optional
        Path to the configuration file (default is "./env_variables.json").
    """
    self.configs: List[ContainerConfig] = load_configs(file_path)
    self.state: List[ContainerConfig] = self.configs.copy()
    self.plot_cache: Dict[str, go.Layout] = {}
    self.data_buffers: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    self.max_buffer_size: int = 96

    if not self.configs:
      logger.error('No configurations loaded. Exiting application.')
      sys.exit(1)

  async def update_consumption_data(self) -> None:
    """
    Fetches and updates consumption data for each container.

    Returns
    -------
    None
    """
    async with aiohttp.ClientSession() as session:
      tasks = []
      for config in self.configs:
        is_local = os.getenv('DOCKER_ENVIRONMENT', 'true') == 'false'
        base_url = 'http://localhost' if is_local else config.vtn_self_host

        # Fetch consumption data
        consumption_url = f'{base_url}:{config.rest_api_port}/data/consumption'
        tasks.append(fetch_data_async(session, consumption_url))

      results = await asyncio.gather(*tasks)
      for idx, config in enumerate(self.configs):
        consumption_data = results[idx]
        if consumption_data:
          buffer = self.data_buffers.setdefault(
            config.container_name, {'consumption': [], 'load_profile': []}
          )
          buffer['consumption'].append(consumption_data['consumption'])
          if len(buffer['consumption']) > self.max_buffer_size:
            buffer['consumption'].pop(0)

        logger.info(f'Updated buffer for {config.container_name} (consumption)')

  async def update_load_profile_data(self) -> None:
    """
    Fetches and updates load profile data for each container.

    Returns
    -------
    None
    """
    async with aiohttp.ClientSession() as session:
      tasks = [
        self._fetch_load_profile_data(session, config) for config in self.configs
      ]
      results = await asyncio.gather(*tasks)
      for idx, config in enumerate(self.configs):
        self._process_load_profile_data(config, results[idx])

  @staticmethod
  async def _fetch_load_profile_data(
    session: aiohttp.ClientSession, config: ContainerConfig
  ) -> Optional[Dict[str, Any]]:
    is_local = os.getenv('DOCKER_ENVIRONMENT', 'true') == 'false'
    base_url = 'http://localhost' if is_local else config.vtn_self_host
    load_profile_url = f'{base_url}:{config.rest_api_port}/data/load_profile'
    return await fetch_data_async(session, load_profile_url)

  def _process_load_profile_data(
    self, config: ContainerConfig, load_profile_data: Optional[Dict[str, Any]]
  ) -> None:
    if load_profile_data:
      buffer = self.data_buffers.setdefault(
        config.container_name, {'consumption': [], 'load_profile': []}
      )
      if 'value' in load_profile_data and isinstance(load_profile_data['value'], dict):
        for time, value in load_profile_data['value'].items():
          buffer['load_profile'].append({'timestamp': time, 'value': value})
        if len(buffer['load_profile']) > self.max_buffer_size:
          buffer['load_profile'] = buffer['load_profile'][-self.max_buffer_size :]
      else:
        logger.error(f'Unexpected format for load profile data: {load_profile_data}')
      logger.info(f'Updated buffer for {config.container_name} (load_profile)')

  @staticmethod
  def parse_time_to_datetime(time_str: str) -> datetime:
    """
    Parses a time string in 'HH:MM' format to a datetime object with today's date.

    Parameters
    ----------
    time_str : str
        Time string in 'HH:MM' format.

    Returns
    -------
    datetime
        Datetime object representing the time on today's date.
    """
    today_str = datetime.now().strftime('%Y-%m-%d')
    timestamp_str = f'{today_str}T{time_str}:00'
    return datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')

  def create_combined_plot(
    self, data: Dict[str, List[Dict[str, Any]]], config: ContainerConfig
  ) -> go.Figure:
    """
    Creates a combined plot of load profile and consumption data for a container.

    Parameters
    ----------
    data : Dict[str, List[Dict[str, Any]]]
        Data to be plotted.
    config : ContainerConfig
        Configuration of the container.

    Returns
    -------
    go.Figure
        Plotly figure object containing the combined plot.
    """
    if config.container_name in self.plot_cache:
      fig = go.Figure(layout=self.plot_cache[config.container_name])
    else:
      fig = self._create_new_plot_layout(config)
      self.plot_cache[config.container_name] = fig.layout

    fig.data = []

    # Plot load profile data first
    load_profile_data = data.get('load_profile', [])
    if load_profile_data:
      load_profile_times = []
      load_profile_values = []
      for entry in load_profile_data:
        timestamp = self.parse_time_to_datetime(entry['timestamp'])
        load_profile_times.append(timestamp)
        load_profile_values.append(entry['value'])

      sorted_indices = sorted(
        range(len(load_profile_times)), key=lambda i: load_profile_times[i]
      )
      load_profile_times = [load_profile_times[i] for i in sorted_indices]
      load_profile_values = [load_profile_values[i] for i in sorted_indices]

      fig.add_trace(
        go.Scatter(
          x=load_profile_times,
          y=load_profile_values,
          mode='lines+markers',
          name='Load Profile',
          line=dict(color='rgba(24, 115, 250, 0.6)'),
          marker=dict(size=8, color='rgba(24, 115, 250, 1.0)'),
          fill='tozeroy',  # Fill the area below the line
          fillcolor='rgba(24, 115, 250, 0.2)',  # Semi-transparent fill color
        )
      )

    # Plot consumption data second
    consumption_data = data.get('consumption', [])
    if consumption_data:
      consumption_times = []
      consumption_values = []
      for entry in consumption_data:
        try:
          timestamp = datetime.strptime(entry['timestamp'], '%Y-%m-%dT%H:%M:%S.%f')
        except ValueError:
          timestamp = datetime.strptime(entry['timestamp'], '%Y-%m-%dT%H:%M:%S')
        timestamp = round_to_nearest_minute(timestamp)
        consumption_times.append(timestamp)
        consumption_values.append(entry['value'])

      sorted_indices = sorted(
        range(len(consumption_times)), key=lambda i: consumption_times[i]
      )
      consumption_times = [consumption_times[i] for i in sorted_indices]
      consumption_values = [consumption_values[i] for i in sorted_indices]

      fig.add_trace(
        go.Scatter(
          x=consumption_times,
          y=consumption_values,
          mode='lines+markers',
          name='Consumption',
          line=dict(color='rgba(250, 115, 24, 0.6)'),
          marker=dict(size=8, color='rgba(250, 115, 24, 1.0)'),
          fill='tozeroy',  # Fill the area below the line
          fillcolor='rgba(250, 115, 24, 0.2)',  # Semi-transparent fill color
        )
      )

    return fig

  @staticmethod
  def _create_new_plot_layout(config: ContainerConfig) -> go.Figure:
    """
    Creates a new plot layout for a container.

    Parameters
    ----------
    config : ContainerConfig
        Configuration of the container.

    Returns
    -------
    go.Figure
        Plotly figure object with the new layout.
    """
    return go.Figure(
      layout=dict(
        title={
          'text': f'{config.container_name} - Port {config.rest_api_port}',
          'font': {'color': 'white'},
        },
        xaxis=dict(
          title='Time',
          title_font_color='white',
          tickfont_color='white',
          gridcolor='rgba(255,255,255,0.2)',
          fixedrange=True,
        ),
        yaxis=dict(
          title='Value',
          title_font_color='white',
          tickfont_color='white',
          gridcolor='rgba(255,255,255,0.2)',
          fixedrange=True,
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        template='plotly_dark',
        margin=dict(l=50, r=50, t=50, b=50),
        height=400,
      )
    )

  def update_state(self, new_state: List[ContainerConfig]) -> None:
    """
    Updates the current state with a new state.

    Parameters
    ----------
    new_state : List[ContainerConfig]
        New state to be set.

    Returns
    -------
    None
    """
    self.state = new_state

  def add_to_state(self, config: ContainerConfig) -> None:
    """
    Adds a single configuration to the current state.

    Parameters
    ----------
    config : ContainerConfig
        Configuration to be added.

    Returns
    -------
    None
    """
    self.state = [config]

  def add_all_to_state(self) -> None:
    """
    Adds all configurations to the current state.

    Returns
    -------
    None
    """
    self.state = self.configs.copy()

  def add_layer_to_state(self, layer: int) -> None:
    """
    Adds configurations of a specific layer to the current state.

    Parameters
    ----------
    layer : int
        Layer number to filter configurations by.

    Returns
    -------
    None
    """
    self.state = [config for config in self.configs if config.layer == layer]

  def get_unique_layers(self) -> List[int]:
    """
    Gets a list of unique layers from the configurations.

    Returns
    -------
    List[int]
        List of unique layer numbers.
    """
    return sorted({config.layer for config in self.configs})

  def create_interface(self) -> gr.Blocks:
    """
    Creates the Gradio interface for the dashboard.

    Returns
    -------
    gr.Blocks
        Gradio interface blocks.
    """
    css = self._get_css_styles()
    with gr.Blocks(css=css) as interface:
      self.add_all_to_state()
      state_var = gr.State(self.state)

      self._create_layout(state_var)

      def update_plots(state: List[ContainerConfig]) -> List[gr.Plot]:
        outputs = [gr.Plot(visible=False) for _ in self.plot_components]

        if not state:
          return outputs

        for idx, config in enumerate(state):
          buffer = self.data_buffers.get(
            config.container_name, {'consumption': [], 'load_profile': []}
          )
          plot = self.create_combined_plot(buffer, config)
          outputs[idx] = gr.Plot(value=plot, visible=True)

        return outputs

      timer_load_profile = gr.Timer(5)
      timer_consumption_data = gr.Timer(60)
      timer_load_profile.tick(
        lambda: asyncio.run(self.update_load_profile_data()), [], []
      )
      timer_consumption_data.tick(
        lambda: asyncio.run(self.update_consumption_data()), [], []
      )
      timer_load_profile.tick(
        update_plots, inputs=[state_var], outputs=self.plot_components
      )

      interface.load(update_plots, inputs=[state_var], outputs=self.plot_components)
      state_var.change(update_plots, inputs=[state_var], outputs=self.plot_components)

      return interface

  @staticmethod
  def _get_css_styles() -> str:
    """
    Returns CSS styles for the Gradio interface.

    Returns
    -------
    str
        CSS styles.
    """
    return """
            .gradio-container { max-width: 100% !important; padding: 0 !important; min-height: 100vh; }
            #dashboard-layout { display: flex; min-height: 100vh; }
            #sidebar { position: fixed; top: 0; left: 0; width: 250px; height: 100vh;
                      background-color: #1a1a1a; padding: 1rem; border-right: 1px solid #333;
                      overflow-y: auto; }
            #main-content { margin-left: 316px; flex: 1; padding: 1rem; overflow-y: auto; }
        """

  def _create_layout(self, state_var: gr.State) -> None:
    """
    Creates the layout for the dashboard.

    Parameters
    ----------
    state_var : gr.State
        State variable for the Gradio interface.

    Returns
    -------
    None
    """
    with gr.Row(elem_id='dashboard-layout'):
      self._create_sidebar(state_var)
      self._create_main_content()

  def _create_sidebar(self, state_var: gr.State) -> None:
    """
    Creates the sidebar for the dashboard.

    Parameters
    ----------
    state_var : gr.State
        State variable for the Gradio interface.

    Returns
    -------
    None
    """
    with gr.Column(elem_id='sidebar', scale=1):
      with gr.Accordion('Layers', open=True):
        gr.Button('General Overview').click(
          lambda: self.add_all_to_state() or self.state,
          inputs=None,
          outputs=state_var,
        )

        for layer in self.get_unique_layers():
          gr.Button(f'Layer {layer} Overview').click(
            lambda layer_num=layer: self.add_layer_to_state(layer_num) or self.state,
            inputs=None,
            outputs=state_var,
          )

        self._create_layer_buttons(state_var)

  def _create_layer_buttons(self, state_var: gr.State) -> None:
    """
    Creates buttons for each layer in the sidebar.

    Parameters
    ----------
    state_var : gr.State
        State variable for the Gradio interface.

    Returns
    -------
    None
    """
    max_layer = max(config.layer for config in self.configs)
    for layer in range(max_layer + 1):
      with gr.Accordion(f'Layer {layer}', open=False):
        for config in self.configs:
          if config.layer == layer:
            gr.Button(f'{config.container_name} {config.rest_api_port}').click(
              lambda c=config: self.add_to_state(c) or self.state,
              inputs=None,
              outputs=state_var,
            )

  def _create_main_content(self) -> None:
    """
    Creates the main content area for the dashboard.

    Returns
    -------
    None
    """
    with gr.Column(elem_id='main-content', scale=4):
      with gr.Blocks(elem_classes='plot-grid'):
        self.plot_components = [
          gr.Plot(visible=False, elem_classes='plot-container')
          for _ in range(len(self.configs))
        ]

  def _update_plot_components(self, state: List[ContainerConfig]) -> List[gr.Plot]:
    """
    Updates the plot components based on the current state.

    Parameters
    ----------
    state : List[ContainerConfig]
        Current state of the dashboard.

    Returns
    -------
    List[gr.Plot]
        List of Gradio plot components.
    """
    outputs = [gr.Plot(visible=False) for _ in self.plot_components]

    if not state:
      return outputs

    for idx, config in enumerate(state):
      buffer = self.data_buffers.get(
        config.container_name, {'consumption': [], 'load_profile': []}
      )
      plot = self.create_combined_plot(buffer, config)
      outputs[idx] = gr.Plot(value=plot, visible=True)

    return outputs
