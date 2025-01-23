# src/ui/components/chart.py
from typing import List
import plotly.graph_objects as go

from src.adr_node.mock_node_dashboard.utils.time_utils import TimeUtils


class ChartComponent:
  def __init__(
    self,
    title: str = 'Load Profile Visualization',
    height: int = 400,
    line_color: str = 'rgba(250, 115, 24, 0.6)',
    marker_color: str = 'rgba(250, 115, 24, 1.0)',
  ):
    self.title = title
    self.height = height
    self.line_color = line_color
    self.marker_color = marker_color

  def create_figure(self, values: List[int], times: List[str] = None) -> go.Figure:
    """
    Create a Plotly figure for the slider values.

    Args:
        values: List of slider values
        times: Optional list of time labels for x-axis

    Returns:
        Plotly Figure object
    """
    if times is None:
      times = TimeUtils.generate_hour_labels(len(values))

    fig = go.Figure(
      data=[
        go.Scatter(
          x=times,
          y=values,
          mode='lines+markers',
          line=dict(color=self.line_color),
          marker=dict(size=8, color=self.marker_color),
        )
      ]
    )

    fig.update_layout(
      title={'text': self.title, 'font': {'color': 'white'}},
      xaxis_title='Time',
      yaxis_title='Load (kWh)',
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
      height=self.height,
      plot_bgcolor='rgba(0,0,0,0)',
      paper_bgcolor='rgba(0,0,0,0)',
      font_color='white',
      template='plotly_dark',
    )

    return fig

  def update_figure(
    self, fig: go.Figure, values: List[int], times: List[str] = None
  ) -> go.Figure:
    """
    Update an existing figure with new values.

    Args:
        fig: Existing Plotly figure
        values: New values to display
        times: Optional new time labels

    Returns:
        Updated Plotly figure
    """
    if times is None:
      times = TimeUtils.generate_hour_labels(len(values))

    fig.data[0].x = times
    fig.data[0].y = values
    return fig
