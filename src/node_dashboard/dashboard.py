import json
import logging
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import asyncio
import aiohttp
from datetime import datetime, timedelta

import gradio as gr
import plotly.graph_objs as go

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ContainerConfig:
  vtn_name: str
  vtn_url: str
  vtn_path_prefix: str
  ven_name: str
  gradio_port: str
  gradio_server_name: str
  rest_api_port: str
  vtn_self_host: str
  layer: int
  container_name: str


class GradioNodeDashboard:
  def __init__(self, file_path: str = './env_variables.json') -> None:
    self.configs: List[ContainerConfig] = []
    self.state: List[ContainerConfig] = []
    self.file_path: str = file_path
    self.plot_cache: Dict[str, go.Layout] = {}
    self.data_buffers: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    self.max_buffer_size: int = 96

    self._load_configs()
    if not self.configs:
      logger.error('No configurations loaded. Exiting application.')
      sys.exit(1)

  def _load_configs(self) -> None:
    try:
      with open(self.file_path) as f:
        data = json.load(f)
        for container_name, values in data.items():
          config = {
            'vtn_name': values['VTN_NAME'],
            'vtn_url': values['VTN_URL'],
            'vtn_path_prefix': values['VTN_PATH_PREFIX'],
            'ven_name': values['VEN_NAME'],
            'gradio_port': values['GRADIO_PORT'],
            'gradio_server_name': values['GRADIO_SERVER_NAME'],
            'rest_api_port': values['REST_API_PORT'],
            'vtn_self_host': values['VTN_SELF_HOST'],
            'layer': int(values['LAYER']),
            'container_name': container_name,
          }
          self.configs.append(ContainerConfig(**config))
    except FileNotFoundError:
      logger.error(f'Config file not found: {self.file_path}')
    except json.JSONDecodeError as e:
      logger.error(f'Invalid JSON in config file: {e}')

  async def fetch_data_async(
    self, session: aiohttp.ClientSession, url: str
  ) -> Optional[Dict[str, Any]]:
    logger.info(f'Fetching data from {url}')
    try:
      async with session.get(url, timeout=10) as response:  # Increased timeout
        response.raise_for_status()
        return await response.json()
    except aiohttp.ClientError as e:
      logger.error(f'Failed to fetch data: {e} from {url}')
      return None

  async def update_data_buffers(self) -> None:
    async with aiohttp.ClientSession() as session:
      tasks = []
      for config in self.configs:
        is_local = os.getenv('DOCKER_ENVIRONMENT', 'true') == 'false'
        base_url = 'http://localhost' if is_local else config.vtn_self_host

        # Fetch consumption data
        consumption_url = f'{base_url}:{config.rest_api_port}/data/consumption'
        tasks.append(self.fetch_data_async(session, consumption_url))

        # Fetch load profile data
        load_profile_url = f'{base_url}:{config.rest_api_port}/data/load_profile'
        tasks.append(self.fetch_data_async(session, load_profile_url))

      results = await asyncio.gather(*tasks)
      for idx, config in enumerate(self.configs):
        consumption_data = results[idx * 2]
        load_profile_data = results[idx * 2 + 1]

        if consumption_data:
          buffer = self.data_buffers.setdefault(
            config.container_name, {'consumption': [], 'load_profile': []}
          )
          buffer['consumption'].append(consumption_data['consumption'])
          if len(buffer['consumption']) > self.max_buffer_size:
            buffer['consumption'].pop(0)

        if load_profile_data:
          if 'value' in load_profile_data and isinstance(
            load_profile_data['value'], dict
          ):
            for time, value in load_profile_data['value'].items():
              buffer['load_profile'].append({'timestamp': time, 'value': value})
            if len(buffer['load_profile']) > self.max_buffer_size:
              buffer['load_profile'] = buffer['load_profile'][-self.max_buffer_size :]
          else:
            logger.error(
              f'Unexpected format for load profile data: {load_profile_data}'
            )

        logger.info(
          f'Updated buffer for {config.container_name} (load_profile): {buffer["load_profile"]}'
        )
        logger.info(
          f'Updated buffer for {config.container_name} (consumption): {buffer["consumption"]}'
        )

  def round_to_nearest_15_minutes(self, dt: datetime) -> datetime:
    discard = timedelta(
      minutes=dt.minute % 15, seconds=dt.second, microseconds=dt.microsecond
    )
    dt -= discard
    if discard >= timedelta(minutes=7.5):
      dt += timedelta(minutes=15)
    return dt

  def create_combined_plot(
    self, data: Dict[str, List[Dict[str, Any]]], config: ContainerConfig
  ) -> go.Figure:
    if config.container_name in self.plot_cache:
      fig = go.Figure(layout=self.plot_cache[config.container_name])
    else:
      fig = self._create_new_plot_layout(config)
      self.plot_cache[config.container_name] = fig.layout

    fig.data = []

    # Plot load profile data first
    load_profile_data = data.get('load_profile', [])
    today_str = datetime.now().strftime('%Y-%m-%d')
    if load_profile_data:
      load_profile_times = []
      load_profile_values = []
      for entry in load_profile_data:
        timestamp_str = f"{today_str}T{entry['timestamp']}:00"
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')
        load_profile_times.append(timestamp.strftime('%H:%M'))
        load_profile_values.append(entry['value'])

      fig.add_trace(
        go.Scatter(
          x=sorted(load_profile_times),
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
        timestamp = self.round_to_nearest_15_minutes(timestamp).strftime('%H:%M')
        consumption_times.append(timestamp)
        consumption_values.append(entry['value'])

      fig.add_trace(
        go.Scatter(
          x=sorted(consumption_times),
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

  def _create_new_plot_layout(self, config: ContainerConfig) -> go.Figure:
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
    self.state = new_state

  def add_to_state(self, config: ContainerConfig) -> None:
    self.state = [config]

  def add_all_to_state(self) -> None:
    self.state = self.configs.copy()

  def add_layer_to_state(self, layer: int) -> None:
    self.state = [config for config in self.configs if config.layer == layer]

  def get_unique_layers(self) -> List[int]:
    return sorted({config.layer for config in self.configs})

  def create_interface(self) -> gr.Blocks:
    css = self._get_css_styles()
    with gr.Blocks(css=css) as interface:
      self.add_all_to_state()
      state_var = gr.State(self.state)

      self._create_layout(state_var)

      def update_plots(state: List[ContainerConfig]) -> List[gr.Plot]:
        return self._update_plot_components(state)

      timer = gr.Timer(1)
      timer.tick(update_plots, inputs=[state_var], outputs=self.plot_components)
      interface.load(update_plots, inputs=[state_var], outputs=self.plot_components)
      state_var.change(update_plots, inputs=[state_var], outputs=self.plot_components)

      return interface

  def _get_css_styles(self) -> str:
    return """
                .gradio-container { max-width: 100% !important; padding: 0 !important; min-height: 100vh; }
                #dashboard-layout { display: flex; min-height: 100vh; }
                #sidebar { position: fixed; top: 0; left: 0; width: 250px; height: 100vh;
                          background-color: #1a1a1a; padding: 1rem; border-right: 1px solid #333;
                          overflow-y: auto; }
                #main-content { margin-left: 316px; flex: 1; padding: 1rem; overflow-y: auto; }
            """

  def _create_layout(self, state_var: gr.State) -> None:
    with gr.Row(elem_id='dashboard-layout'):
      self._create_sidebar(state_var)
      self._create_main_content()

  def _create_sidebar(self, state_var: gr.State) -> None:
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
    with gr.Column(elem_id='main-content', scale=4):
      with gr.Blocks(elem_classes='plot-grid'):
        self.plot_components = [
          gr.Plot(visible=False, elem_classes='plot-container')
          for _ in range(len(self.configs))
        ]

  def _update_plot_components(self, state: List[ContainerConfig]) -> List[gr.Plot]:
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


def main() -> None:
  dashboard = GradioNodeDashboard()
  interface = dashboard.create_interface()

  async def background_task():
    while True:
      await dashboard.update_data_buffers()
      await asyncio.sleep(60)  # Update every 60 seconds

  loop = asyncio.get_event_loop()
  loop.create_task(background_task())

  interface.launch(server_name='0.0.0.0')


if __name__ == '__main__':
  main()
