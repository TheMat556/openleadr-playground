from typing import Dict, List, Any, Tuple
from datetime import datetime
import plotly.graph_objs as go

from src.network_dashobard.config.container_config import ContainerConfig
from src.network_dashobard.interfaces.iplot_manager import IPlotManager
from src.network_dashobard.services.services import IPlotService, ITimeService


class PlotManager(IPlotManager):
  def __init__(self, plot_service: IPlotService, time_service: ITimeService):
    self.plot_service = plot_service
    self.time_service = time_service
    self.plot_cache: Dict[str, go.Figure] = {}

  def create_combined_plot(
    self,
    data: Dict[str, List[Dict[str, Any]]],
    config: ContainerConfig,
    clear_existing: bool = True,
  ) -> go.Figure:
    """Creates a combined plot of load profile and consumption data"""
    fig = self._get_or_create_figure(config)
    if clear_existing:
      fig.data = []

    # Add load profile trace
    self.plot_service.add_trace(
      fig, data.get('load_profile', []), 'Load Profile', 'blue'
    )

    # Add consumption trace
    self.plot_service.add_trace(
      fig, data.get('consumption', []), 'Consumption', 'orange'
    )

    return fig

  def _get_or_create_figure(self, config: ContainerConfig) -> go.Figure:
    """Gets or creates a new figure for the container"""
    if config.container_name not in self.plot_cache:
      self.plot_cache[config.container_name] = self.plot_service.create_figure(config)
    return self.plot_cache[config.container_name]

  def _process_data_points(
    self, data: List[Dict[str, Any]]
  ) -> Tuple[List[datetime], List[float]]:
    """Processes data points for plotting"""
    return self.plot_service.process_data_points(data)
