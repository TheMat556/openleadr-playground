import json
from dataclasses import dataclass

import requests
import pandas as pd
import gradio as gr
import plotly.graph_objs as go
from gradio import Timer

@dataclass
class ContainerConfig:
    vtn_name: str
    vtn_url: str
    vtn_path_prefix: str
    ven_name: str
    gradio_port: str
    gradio_server_name: str
    rest_api_port: str
    adr_mapping_port: str

class GradioNodeDashboard:
    def __init__(self, file_path="../../env_variables.json"):
        self.configs = []
        self.file_path = file_path

        self.load_configs(file_path)
        print("Configs loaded: ", self.configs)

    def load_configs(self, file_path):
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
                    'adr_mapping_port': value['ADR_MAPPING_PORT']
                }
                self.configs.append(ContainerConfig(**config))

    def fetch_data(self, rest_api_port):
        url = f'http://localhost:{rest_api_port}/data/load_profile'
        response = requests.get(url)
        response.raise_for_status()
        return json.loads(response.json())

    def process_data(self, data):
        time_values = [(v['time'], v['value']) for v in data.values()]
        df = pd.DataFrame(time_values, columns=['time', 'value'])
        return df

    def create_plot(self, df):
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
            title={'text': 'Data Plot', 'font': {'color': 'white'}},
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

    def update_plot1(self):
      print("update data")
      # Create a dummy DataFrame with some sample data
      data = {
        'time': pd.date_range(start='2024-01-01', periods=10, freq='H'),
        'value': range(10)
      }
      df = pd.DataFrame(data)
      return df

    def update_plot(self, rest_api_port):
        data = self.fetch_data(rest_api_port)
        df = self.process_data(data)
        return self.create_plot(df)

    def create_interface(self):
        with gr.Blocks(css='.gradio-container { max-width: 95% !important; }') as interface:
            with gr.Row():
                for config in self.configs:
                    with gr.Column():
                      plot_output = gr.Plot(
                        value=lambda: self.update_plot(config.rest_api_port),
                        every=Timer(5))
        return interface

if __name__ == '__main__':
    gradio_node_dashboard = GradioNodeDashboard()
    interface = gradio_node_dashboard.create_interface()
    interface.launch(share=False)
