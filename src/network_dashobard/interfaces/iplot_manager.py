from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple
import plotly.graph_objs as go
from datetime import datetime

from src.network_dashobard.config.container_config import ContainerConfig


class IPlotManager(ABC):
  @abstractmethod
  def create_combined_plot(
    self,
    data: Dict[str, List[Dict[str, Any]]],
    config: ContainerConfig,
    clear_existing: bool = True,
  ) -> go.Figure:
    pass

  @abstractmethod
  def _process_data_points(
    self, data: List[Dict[str, Any]]
  ) -> Tuple[List[datetime], List[float]]:
    pass
