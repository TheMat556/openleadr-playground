from typing import Protocol, Dict, Any, List, Tuple
from datetime import datetime
import plotly.graph_objs as go
import gradio as gr

from src.network_dashobard.config.container_config import ContainerConfig


class IHttpClient(Protocol):
  async def fetch_data(
    self, config: ContainerConfig, endpoint: str
  ) -> Dict[str, Any]: ...


class ITimeService(Protocol):
  def convert_timestamp(self, timestamp: int) -> int: ...

  def parse_datetime(self, time_str: str) -> datetime: ...


class IPlotService(Protocol):
  def create_figure(self, config: ContainerConfig) -> go.Figure: ...

  def add_trace(
    self, fig: go.Figure, data: List[Dict[str, Any]], name: str, color: str
  ) -> None: ...

  def process_data_points(
    self, data: List[Dict[str, Any]]
  ) -> Tuple[List[datetime], List[float]]: ...


class IUIService(Protocol):
  def get_css_styles(self) -> str: ...

  def create_sidebar_components(self, plot_components: Dict[str, gr.Plot]) -> None: ...

  def create_main_content(self, plot_components: Dict[str, gr.Plot]) -> None: ...

  def update_plots(
    self, state: List[ContainerConfig], plot_components: Dict[str, gr.Plot]
  ) -> List[gr.Plot]: ...


class IUpdateService(Protocol):
  def setup_callbacks(self, plot_components: Dict[str, gr.Plot]) -> None: ...
