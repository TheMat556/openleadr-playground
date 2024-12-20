import json
import logging
import os
import sys
from dataclasses import dataclass
from typing import List, Optional

import gradio as gr
import pandas as pd
import requests
import plotly.graph_objs as go


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
        self.state: List[ContainerConfig] = []
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
        if os.getenv('DOCKER_ENVIRONMENT', 'true') == 'false':
            url = f'http://localhost:{rest_api_port}/data/load_profile'
        else:
            url = f'{vtn_self_host}:{rest_api_port}/data/load_profile'
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to fetch data: {e} from {url}')
            return None

    def create_plot(self, data: dict, config: ContainerConfig) -> go.Figure:
        fig = go.Figure(
            data=[
                go.Scatter(
                    x=data['time'],
                    y=data['value'],
                    mode='lines+markers',
                    line=dict(color='rgba(250, 115, 24, 0.6)'),
                    marker=dict(size=8, color='rgba(250, 115, 24, 1.0)'),
                )
            ]
        )
        fig.update_layout(
            title={'text': f'{config.container_name} - Port {config.rest_api_port}', 'font': {'color': 'white'}},
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
            margin=dict(l=50, r=50, t=50, b=50)
        )
        return fig

    def add_to_state(self, config: ContainerConfig) -> None:
        self.state = [config]

    def add_all_to_state(self) -> None:
        self.state = self.configs.copy()

    def add_layer_to_state(self, layer: int) -> None:
        self.state = [config for config in self.configs if config.layer == layer]

    def get_unique_layers(self) -> List[int]:
        return sorted(set(config.layer for config in self.configs))

    def create_interface(self) -> gr.Blocks:
      with gr.Blocks(
        css="""
                .gradio-container { max-width: 95% !important; background-color: black; }
                .full-height { height: 100%; display: flex; flex-wrap: wrap; }
                .plot-container { min-width: 400px; flex: 1; margin: 10px; }
                """
      ) as interface:
        state_var = gr.State(self.state)

        with gr.Row():
          with gr.Column(visible=True, scale=4) as main_content:
            # Create a list of Plot components based on the maximum number of configs
            plot_components = [gr.Plot(visible=False) for _ in range(len(self.configs))]

          with gr.Column(visible=True, min_width=200, scale=1) as sidebar:
            with gr.Accordion("Layers", open=True):
              gr.Button("General Overview").click(
                lambda: self.add_all_to_state() or self.state,
                inputs=None,
                outputs=state_var
              )

              unique_layers = self.get_unique_layers()
              for layer in unique_layers:
                gr.Button(f"Layer {layer} Overview").click(
                  lambda l=layer: self.add_layer_to_state(l) or self.state,
                  inputs=None,
                  outputs=state_var
                )

              max_layer = max(config.layer for config in self.configs)
              for layer in range(max_layer + 1):
                with gr.Accordion(f"Layer {layer}", open=False):
                  for config in self.configs:
                    if config.layer == layer:
                      gr.Button(
                        f"{config.container_name} {config.rest_api_port}").click(
                        lambda c=config: self.add_to_state(c) or self.state,
                        inputs=None,
                        outputs=state_var
                      )

        def update_plots(state):
          # Reset all plots to invisible
          outputs = [gr.Plot(visible=False) for _ in plot_components]

          if state:
            for idx, config in enumerate(state):
              data = self.fetch_data(config.vtn_self_host, config.rest_api_port)
              if data:
                df = pd.DataFrame(data)
                df.reset_index(inplace=True)
                df.columns.values[0] = 'time'

                fig = self.create_plot(df.to_dict(orient='list'), config)
                outputs[idx] = gr.Plot(value=fig, visible=True)

          return outputs

        state_var.change(
          update_plots,
          inputs=[state_var],
          outputs=plot_components
        )

      return interface
