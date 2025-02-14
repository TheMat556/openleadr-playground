from typing import Dict, List, Any, Tuple
from datetime import datetime

import logging
import plotly.graph_objs as go

from src.network_dashobard.config.container_config import ContainerConfig
from src.network_dashobard.services.services import IPlotService


class PlotService(IPlotService):
  def create_figure(self, config: ContainerConfig) -> go.Figure:
    """Creates a new plot figure with proper layout"""
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
        autosize=True,
      )
    )

  def add_trace(
    self, fig: go.Figure, data: List[Dict[str, Any]], name: str, color: str
  ) -> None:
    """Adds a trace to the figure"""
    if not data:
      logging.debug(f'No data to add for trace: {name}')
      return

    times, values = self.process_data_points(data)
    if not times or not values:
      return

    # Sort by time
    combined = sorted(zip(times, values), key=lambda x: x[0])
    sorted_times, sorted_values = zip(*combined)

    # Add trace
    fig.add_trace(
      go.Scatter(
        x=sorted_times,
        y=sorted_values,
        mode='lines+markers',
        name=name,
        line=dict(color=f'rgba{self._get_color_rgba(color, 0.6)}'),
        marker=dict(
          size=8,
          color=f'rgba{self._get_color_rgba(color, 1.0)}',
        ),
        fill='tozeroy',
        fillcolor=f'rgba{self._get_color_rgba(color, 0.2)}',
      )
    )

  def process_data_points(
    self, data: List[Dict[str, Any]]
  ) -> Tuple[List[datetime], List[float]]:
    """Process data points for plotting"""
    times = []
    values = []

    for point in data:
      try:
        if 'signal_payload' in point:
          timestamp = datetime.fromtimestamp(point['timestamp'] / 1000)
          value = point['signal_payload']
        elif 'value' in point:
          timestamp = datetime.fromtimestamp(int(point['timestamp']) / 1000)
          value = point['value']
        else:
          continue

        times.append(timestamp)
        values.append(value)
      except (ValueError, TypeError) as e:
        logging.warning(f'Invalid data point format: {point}. Error: {e}')
        continue

    return times, values

  def _get_color_rgba(self, color: str, alpha: float) -> str:
    """Converts color name to RGBA tuple string"""
    color_map = {
      'blue': (24, 115, 250),
      'orange': (250, 115, 24),
      'green': (24, 250, 115),
      'red': (250, 24, 24),
    }
    rgb = color_map.get(color.lower(), (128, 128, 128))
    return f'({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})'
