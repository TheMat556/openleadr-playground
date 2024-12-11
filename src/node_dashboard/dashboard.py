import json
import logging
from dataclasses import dataclass
from io import StringIO

import requests
import pandas as pd
import gradio as gr
import plotly.graph_objs as go
from gradio import Timer


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
  adr_mapping_port: str


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GradioNodeDashboard:
  def __init__(self, file_path='./env_variables.json'):
    self.configs = []
    self.file_path = file_path

    self.load_configs(file_path)

  def load_configs(self, file_path):
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
            'adr_mapping_port': value['ADR_MAPPING_PORT'],
          }
          self.configs.append(ContainerConfig(**config))
    except FileNotFoundError:
      logging.error(f'Config file not found: {file_path}')
    except json.JSONDecodeError as e:
      logging.error(f'Invalid JSON in config file: {e}')

  def fetch_data(self, rest_api_port):
    url = f'http://localhost:{rest_api_port}/data/load_profile'
    try:
      response = requests.get(url)
      response.raise_for_status()
      return response.json()
    except requests.exceptions.RequestException as e:
      logger.error(f'Failed to fetch data: {e}')
      return None

  def process_data(self, data):
    try:
      json_str = json.dumps(data)  # Convert dictionary to JSON string
      df = pd.read_json(StringIO(json_str))  # Wrap JSON string in StringIO

      # Reset the index to make 'time' a column
      df.reset_index(inplace=True)

      # Rename the columns
      df.columns = ['time', 'value']

      return df
    except Exception as e:
      logging.error(f'Failed to process data: {e}')
      return pd.DataFrame(
        columns=['time', 'value']
      )  # Return an empty DataFrame in case of an error

  def create_plot(self, df, port):
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

  def update_plot(self, rest_api_port):
    data = self.fetch_data(rest_api_port)
    if data is not None:
      df = self.process_data(data)
      return self.create_plot(df, rest_api_port)
    else:
      return None  # Return None if data is None

  def create_interface(self):
    with gr.Blocks(
      css="""
            .gradio-container { max-width: 95% !important; background-color: black; }
            .full-height { height: 100%; display: flex; align-items: center; justify-content: center; }
            """
    ) as interface:
      with gr.Row():
        for env_config in self.configs:
          with gr.Column():

            def plot(config=env_config):
              return self.update_plot(config.rest_api_port)

            if plot() is not None:
              gr.Plot(value=plot, every=Timer(5), label=env_config.vtn_name)
            else:
              gr.Label(
                value=lambda config=env_config: f'⚠ No data available for {config.vtn_name}',
                every=Timer(5),
              )
    return interface
