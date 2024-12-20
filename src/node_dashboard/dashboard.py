import json
import logging
import os
import sys
from dataclasses import dataclass
from io import StringIO
from typing import List, Optional

import requests
import pandas as pd
import gradio as gr
import plotly.graph_objs as go
from gradio import Timer
from numpy import flexible


@dataclass
class ContainerConfig:
  """Configuration for container settings including VTN, VEN, and port information."""

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


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GradioNodeDashboard:
  def __init__(self, file_path: str = './env_variables.json') -> None:
    self.configs: List[ContainerConfig] = []
    self.file_path = file_path

    self.load_configs(file_path)
    if not self.configs:
      logger.error('No configurations loaded. Exiting application.')
      sys.exit(1)

  def load_configs(self, file_path: str) -> None:
    try:
      with open(file_path) as f:
        data = json.load(f)
        for key, value in data.items():
          config = {
            'vtn_name': value['VTN_NAME'],
            'vtn_url': value['VTN_URL'],
            'vtn_path_prefix': value['VTN_PATH_PREFIX'],
            'ven_name': value['VEN_NAME'],
            'gradio_port': value['GRADIO_PORT'],
            'gradio_server_name': value['GRADIO_SERVER_NAME'],
            'rest_api_port': value['REST_API_PORT'],
            'vtn_self_host': value['VTN_SELF_HOST'],
            'layer': int(value['LAYER']),
            'container_name': key,
          }
          self.configs.append(ContainerConfig(**config))
    except FileNotFoundError:
      logger.error(f'Config file not found: {file_path}')
    except json.JSONDecodeError as e:
      logger.error(f'Invalid JSON in config file: {e}')

  def fetch_data(self, vtn_self_host: str, rest_api_port: str) -> Optional[dict]:
    print("FETCH DATA")
    if os.getenv('DOCKER_ENVIRONMENT', 'true') == 'false':
      url = f'http://localhost:{rest_api_port}/data/load_profile'
    else:
      url = f'{vtn_self_host}:{rest_api_port}/data/load_profile'
    print("URL", url)
    try:
      response = requests.get(url)
      response.raise_for_status()
      return response.json()
    except requests.exceptions.RequestException as e:
      logger.error(f'Failed to fetch data: {e} from {url}')
      return None

  def process_data(self, data: dict) -> pd.DataFrame:
    try:
      json_str = json.dumps(data)  # Convert dictionary to JSON string
      df = pd.read_json(StringIO(json_str))  # Wrap JSON string in StringIO

      # Reset the index to make 'time' a column
      df.reset_index(inplace=True)

      # Rename the columns
      df.columns = ['time', 'value']

      return df
    except Exception as e:
      logger.error(f'Failed to process data: {e}')
      return pd.DataFrame(
        columns=['time', 'value']
      )  # Return an empty DataFrame in case of an error

  def create_plot(self, df: pd.DataFrame, port: str) -> go.Figure:
    fig = go.Figure(
      data=[
        go.Scatter(
          x=df['time'],
          y=df['value'],
          mode='lines+markers',
          line=dict(color='rgba(250, 115, 24, 0.6)'),
          marker=dict(size=8, color='rgba(250, 115, 24, 1.0)'),
        )
      ]
    )
    fig.update_layout(
      title={'text': f'Data {port}', 'font': {'color': 'white'}},
      xaxis_title='Time',
      yaxis_title='Value',
      xaxis=dict(
        title_font_color='white',
        tickfont_color='white',
        gridcolor='rgba(255,255,255,0.2)',
      ),
      yaxis=dict(
        title_font_color='white',
        tickfont_color='white',
        gridcolor='rgba(255,255,255,0.2)',
      ),
      height=400,
      plot_bgcolor='rgba(0,0,0,0)',
      paper_bgcolor='rgba(0,0,0,0)',
      font_color='white',
      template='plotly_dark',
    )
    return fig

  def update_plot(self, vtn_self_host: str, rest_api_port: str) -> Optional[go.Figure]:
    data = self.fetch_data(vtn_self_host, rest_api_port)
    if data is not None:
      df = self.process_data(data)
      return self.create_plot(df, rest_api_port)
    else:
      return None  # Return None if data is None

  def create_interface(self) -> gr.Blocks:
    with gr.Blocks(
      css="""
              .gradio-container { max-width: 95% !important; background-color: black; }
              .full-height { height: 100%; display: flex; align-items: center; justify-content: center; }
              """
    ) as interface:
      with gr.Row():
        with gr.Column(visible=True, scale=4) as x:  # Set scale to a higher value
          plot_output = gr.Plot(label="Layer 0 Plot",
                                value=self.update_plot(vtn_self_host='',
                                                       rest_api_port='5000'))
        with gr.Column(visible=True, min_width=200, scale=1) as sidebar:
          with gr.Accordion("Layers", open=True):
            max_layer = max(config.layer for config in self.configs)
            for layer in range(max_layer + 1):
              with gr.Accordion(f"Layer {layer}", open=False):
                for config in self.configs:
                  if config.layer == layer:
                    gr.Button(f"{config.container_name} {config.rest_api_port}",
                              value=config.layer,
                              elem_id=f"{config.container_name}_btn").click(
                      lambda c=config: self.update_plot(rest_api_port=c.rest_api_port,
                                                        vtn_self_host=c.vtn_self_host),
                      # Pass the correct config value
                      inputs=None,
                      outputs=plot_output
                    )

    return interface
