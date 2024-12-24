"""
Gradio Dashboard for Node Visualization and Monitoring.

This module provides a real-time dashboard for visualizing and monitoring node data
using Gradio. It supports multiple layers of nodes and provides an interactive
interface for data visualization.

Example:
    To run the dashboard::

        $ python dashboard.py

Requirements:
    - gradio
    - pandas
    - plotly
    - requests

Author: Updated version with improved code quality
Date: December 2024
"""

import json
import logging
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Union, Any

import gradio as gr
import pandas as pd
import plotly.graph_objs as go
import requests
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ContainerConfig:
    """Configuration dataclass for container settings.

    Attributes:
        vtn_name (str): Virtual Top Node name
        vtn_url (str): VTN URL endpoint
        vtn_path_prefix (str): Path prefix for VTN
        ven_name (str): Virtual End Node name
        gradio_port (str): Port for Gradio interface
        gradio_server_name (str): Server name for Gradio
        rest_api_port (str): Port for REST API
        vtn_self_host (str): VTN self-host address
        layer (int): Layer number in hierarchy
        container_name (str): Name of the container
    """

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
    """
    A dashboard class for visualizing node data using Gradio interface.

    This class handles the creation and management of a real-time dashboard
    for monitoring node data across different layers.
    """

    def __init__(self, file_path: str = "./env_variables.json") -> None:
        """
        Initialize the dashboard with configuration from a JSON file.

        Args:
            file_path (str): Path to the configuration JSON file.
                           Defaults to "./env_variables.json".

        Raises:
            SystemExit: If no configurations are loaded successfully.
        """
        self.configs: List[ContainerConfig] = []
        self.state: List[ContainerConfig] = []
        self.file_path: str = file_path
        self.plot_cache: Dict[str, go.Layout] = {}

        self._load_configs()
        if not self.configs:
            logger.error("No configurations loaded. Exiting application.")
            sys.exit(1)

    def _load_configs(self) -> None:
        """
        Load configurations from the JSON file.

        Reads the configuration file and populates the configs list with
        ContainerConfig objects.
        """
        try:
            with open(self.file_path) as f:
                data = json.load(f)
                for container_name, values in data.items():
                    config = {
                        "vtn_name": values["VTN_NAME"],
                        "vtn_url": values["VTN_URL"],
                        "vtn_path_prefix": values["VTN_PATH_PREFIX"],
                        "ven_name": values["VEN_NAME"],
                        "gradio_port": values["GRADIO_PORT"],
                        "gradio_server_name": values["GRADIO_SERVER_NAME"],
                        "rest_api_port": values["REST_API_PORT"],
                        "vtn_self_host": values["VTN_SELF_HOST"],
                        "layer": int(values["LAYER"]),
                        "container_name": container_name,
                    }
                    self.configs.append(ContainerConfig(**config))
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.file_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")

    def fetch_data(
        self, vtn_self_host: str, rest_api_port: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch data from the specified endpoint.

        Args:
            vtn_self_host (str): Host address
            rest_api_port (str): Port number for the REST API

        Returns:
            Optional[Dict[str, Any]]: JSON response data or None if request fails
        """
        is_local = os.getenv("DOCKER_ENVIRONMENT", "true") == "false"
        base_url = "http://localhost" if is_local else vtn_self_host
        url = f"{base_url}:{rest_api_port}/data/load_profile"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logger.error(f"Failed to fetch data: {e} from {url}")
            return None

    def create_plot(
        self, data: Dict[str, List[Union[str, float]]], config: ContainerConfig
    ) -> go.Figure:
        """
        Create or update a plotly figure for the given data.

        Args:
            data (Dict[str, List[Union[str, float]]]): Data for plotting
            config (ContainerConfig): Container configuration

        Returns:
            go.Figure: Plotly figure object
        """
        # Reuse cached layout if available
        if config.container_name in self.plot_cache:
            fig = go.Figure(layout=self.plot_cache[config.container_name])
        else:
            fig = self._create_new_plot_layout(config)
            self.plot_cache[config.container_name] = fig.layout

        # Update data traces
        fig.data = []
        fig.add_trace(
            go.Scatter(
                x=data["time"],
                y=data["value"],
                mode="lines+markers",
                line=dict(color="rgba(250, 115, 24, 0.6)"),
                marker=dict(size=8, color="rgba(250, 115, 24, 1.0)"),
            )
        )
        return fig

    def _create_new_plot_layout(self, config: ContainerConfig) -> go.Figure:
        """
        Create a new plot layout with default styling.

        Args:
            config (ContainerConfig): Container configuration

        Returns:
            go.Figure: Plotly figure with initialized layout
        """
        return go.Figure(
            layout=dict(
                title={
                    "text": f"{config.container_name} - Port {config.rest_api_port}",
                    "font": {"color": "white"},
                },
                xaxis=dict(
                    title="Time",
                    title_font_color="white",
                    tickfont_color="white",
                    gridcolor="rgba(255,255,255,0.2)",
                    fixedrange=True,
                ),
                yaxis=dict(
                    title="Value",
                    title_font_color="white",
                    tickfont_color="white",
                    gridcolor="rgba(255,255,255,0.2)",
                    fixedrange=True,
                ),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                template="plotly_dark",
                margin=dict(l=50, r=50, t=50, b=50),
                height=400,
            )
        )

    def update_state(self, new_state: List[ContainerConfig]) -> None:
        """
        Update the dashboard state with new configuration.

        Args:
            new_state (List[ContainerConfig]): New state configuration
        """
        self.state = new_state

    def add_to_state(self, config: ContainerConfig) -> None:
        """
        Add a single configuration to the state.

        Args:
            config (ContainerConfig): Configuration to add
        """
        self.state = [config]

    def add_all_to_state(self) -> None:
        """Add all configurations to the state."""
        self.state = self.configs.copy()

    def add_layer_to_state(self, layer: int) -> None:
        """
        Add configurations for a specific layer to the state.

        Args:
            layer (int): Layer number to filter by
        """
        self.state = [config for config in self.configs if config.layer == layer]

    def get_unique_layers(self) -> List[int]:
        """
        Get a sorted list of unique layer numbers.

        Returns:
            List[int]: Sorted list of unique layer numbers
        """
        return sorted({config.layer for config in self.configs})

    def create_interface(self) -> gr.Blocks:
        """
        Create and configure the Gradio interface.

        Returns:
            gr.Blocks: Configured Gradio interface
        """
        css = self._get_css_styles()
        with gr.Blocks(css=css) as interface:
            self.add_all_to_state()
            state_var = gr.State(self.state)

            self._create_layout(state_var)

            def update_plots(state: List[ContainerConfig]) -> List[gr.Plot]:
                return self._update_plot_components(state)

            # Set up periodic updates
            timer = gr.Timer(1)
            timer.tick(update_plots, inputs=[state_var], outputs=self.plot_components)
            interface.load(
                update_plots, inputs=[state_var], outputs=self.plot_components
            )
            state_var.change(
              update_plots, inputs=[state_var], outputs=self.plot_components
            )

            return interface

    def _get_css_styles(self) -> str:
        """
        Get CSS styles for the dashboard.

        Returns:
            str: CSS styles as a string
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
        Create the dashboard layout with sidebar and main content.

        Args:
            state_var (gr.State): Gradio state variable
        """
        with gr.Row(elem_id="dashboard-layout"):
            self._create_sidebar(state_var)
            self._create_main_content()

    def _create_sidebar(self, state_var: gr.State) -> None:
        """
        Create the sidebar with layer controls.

        Args:
            state_var (gr.State): Gradio state variable
        """
        with gr.Column(elem_id="sidebar", scale=1):
            with gr.Accordion("Layers", open=True):
                gr.Button("General Overview").click(
                    lambda: self.add_all_to_state() or self.state,
                    inputs=None,
                    outputs=state_var,
                )

                for layer in self.get_unique_layers():
                    gr.Button(f"Layer {layer} Overview").click(
                        lambda l=layer: self.add_layer_to_state(l) or self.state,
                        inputs=None,
                        outputs=state_var,
                    )

                self._create_layer_buttons(state_var)

    def _create_layer_buttons(self, state_var: gr.State) -> None:
        """
        Create buttons for each layer in the sidebar.

        Args:
            state_var (gr.State): Gradio state variable
        """
        max_layer = max(config.layer for config in self.configs)
        for layer in range(max_layer + 1):
            with gr.Accordion(f"Layer {layer}", open=False):
                for config in self.configs:
                    if config.layer == layer:
                        gr.Button(
                            f"{config.container_name} {config.rest_api_port}"
                        ).click(
                            lambda c=config: self.add_to_state(c) or self.state,
                            inputs=None,
                            outputs=state_var,
                        )

    def _create_main_content(self) -> None:
        """Create the main content area with plot components."""
        with gr.Column(elem_id="main-content", scale=4):
            with gr.Blocks(elem_classes="plot-grid"):
                self.plot_components = [
                    gr.Plot(visible=False, elem_classes="plot-container")
                    for _ in range(len(self.configs))
                ]

    def _update_plot_components(self, state: List[ContainerConfig]) -> List[gr.Plot]:
        """
        Update plot components based on the current state.

        Args:
            state (List[ContainerConfig]): Current state configuration

        Returns:
            List[gr.Plot]: Updated plot components
        """
        outputs = [gr.Plot(visible=False) for _ in self.plot_components]

        if not state:
            return outputs

        for idx, config in enumerate(state):
            data = self.fetch_data(config.vtn_self_host, config.rest_api_port)
            if data:
                df = pd.DataFrame(data).reset_index()
                df.columns.values[0] = "time"
                plot = self.create_plot(df.to_dict(orient="list"), config)
                outputs[idx] = gr.Plot(value=plot, visible=True)

        return outputs


def main() -> None:
    """Main entry point for the dashboard application."""
    dashboard = GradioNodeDashboard()
    interface = dashboard.create_interface()
    interface.launch(server_name="0.0.0.0")


if __name__ == "__main__":
    main()
