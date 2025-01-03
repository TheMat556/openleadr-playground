import logging
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import plotly.graph_objs as go
from .helper.config import ContainerConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlotManager:
  """
  Manages the creation and updating of plots for container data.

  Attributes
  ----------
  plot_cache : Dict[str, go.Figure]
      Cache for plot figures to avoid recreating them.
  """

  def __init__(self):
    """
    Initializes the PlotManager with an empty plot cache.
    """
    self.plot_cache: Dict[str, go.Figure] = {}

  def create_combined_plot(
    self,
    data: Dict[str, List[Dict[str, Any]]],
    config: ContainerConfig,
    clear_existing: bool = True,
  ) -> go.Figure:
    """
    Creates a combined plot of load profile and consumption data for a container.

    Parameters
    ----------
    data : Dict[str, List[Dict[str, Any]]]
        Data to be plotted.
    config : ContainerConfig
        Configuration of the container.
    clear_existing : bool
        Whether to clear existing traces or append new ones.

    Returns
    -------
    go.Figure
        Plotly figure object containing the combined plot.
    """
    fig = self._get_or_create_figure(config)
    if clear_existing:
      fig.data = []  # Clear existing traces

    self._add_trace(
      fig,
      data.get('load_profile', []),
      'Load Profile',
      'rgba(24, 115, 250, 0.6)',
      'rgba(24, 115, 250, 1.0)',
      'rgba(24, 115, 250, 0.2)',
    )
    self._add_trace(
      fig,
      data.get('consumption', []),
      'Consumption',
      'rgba(250, 115, 24, 0.6)',
      'rgba(250, 115, 24, 1.0)',
      'rgba(250, 115, 24, 0.2)',
    )

    return fig

  def _get_or_create_figure(self, config: ContainerConfig) -> go.Figure:
    """
    Gets an existing figure from cache or creates a new one.

    Parameters
    ----------
    config : ContainerConfig
        Configuration of the container.

    Returns
    -------
    go.Figure
        Plotly figure object.
    """
    if config.container_name in self.plot_cache:
      return self.plot_cache[config.container_name]

    fig = self._create_new_plot_layout(config)
    self.plot_cache[config.container_name] = fig
    return fig

  @staticmethod
  def _create_new_plot_layout(config: ContainerConfig) -> go.Figure:
    """
    Creates a new plot layout for a container.

    Parameters
    ----------
    config : ContainerConfig
        Configuration of the container.

    Returns
    -------
    go.Figure
        Plotly figure object with the new layout.
    """
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

  def _add_trace(
    self,
    fig: go.Figure,
    data: List[Dict[str, Any]],
    name: str,
    line_color: str,
    marker_color: str,
    fill_color: str,
  ) -> None:
    """
    Adds a trace to the figure.

    Parameters
    ----------
    fig : go.Figure
        Plotly figure object.
    data : List[Dict[str, Any]]
        Data to be plotted.
    name : str
        Name of the trace.
    line_color : str
        Color of the line.
    marker_color : str
        Color of the markers.
    fill_color : str
        Color of the fill.

    Returns
    -------
    None
    """
    if not data:
      return

    times, values = self._process_data_points(data)
    if times and values:
      fig.add_trace(
        go.Scatter(
          x=times,
          y=values,
          mode='lines+markers',
          name=name,
          line=dict(color=line_color),
          marker=dict(size=8, color=marker_color),
          fill='tozeroy',
          fillcolor=fill_color,
        )
      )

  def _process_data_points(
    self, data: List[Dict[str, Any]]
  ) -> Tuple[List[datetime], List[float]]:
    """
    Process data points for plotting.

    Parameters
    ----------
    data : List[Dict[str, Any]]
        List of data points to process.

    Returns
    -------
    Tuple[List[datetime], List[float]]
        Tuple containing lists of timestamps and values.
    """
    if not data:
      return [], []

    times = []
    values = []

    for point in data:
      # Check if this is load profile data (has 'signal_payload')
      if 'signal_payload' in point:
        timestamp = datetime.fromtimestamp(
          point['timestamp'] / 1000
        )  # Convert from milliseconds
        value = point['signal_payload']
      # Check if this is consumption data (has 'value')
      elif 'value' in point:
        timestamp = datetime.fromtimestamp(
          int(point['timestamp']) / 1000
        )  # Convert string timestamp from milliseconds
        value = point['value']
      else:
        continue

      times.append(timestamp)
      values.append(value)

    return times, values

  @staticmethod
  def _parse_timestamp(timestamp: str) -> Optional[datetime]:
    """
    Parses a Unix timestamp string in milliseconds into a datetime object.

    Parameters
    ----------
    timestamp : str
        Unix timestamp string in milliseconds.

    Returns
    -------
    Optional[datetime]
        Parsed datetime object or None if parsing fails.
    """
    try:
      # Check if the timestamp is a Unix timestamp in milliseconds
      if timestamp.isdigit() and len(timestamp) == 13:
        # Convert milliseconds to seconds and create a datetime object
        return datetime.fromtimestamp(int(timestamp) / 1000, tz=timezone.utc)
      else:
        raise ValueError(f'Invalid Unix timestamp format: {timestamp}')
    except ValueError as e:
      logger.error(f'Invalid timestamp format: {timestamp}. Error: {e}')
      raise

  @staticmethod
  def parse_time_to_datetime(time_str: str, timezone: Optional[str] = None) -> datetime:
    """
    Parses a time string in 'HH:MM' format to a datetime object with today's date.

    Parameters
    ----------
    time_str : str
        Time string in 'HH:MM' format.
    timezone : Optional[str], optional
        Timezone information to be applied, by default None.

    Returns
    -------
    datetime
        Datetime object representing the time on today's date.
    """
    today_str = datetime.now().strftime('%Y-%m-%d')
    timestamp_str = f'{today_str}T{time_str}:00'
    try:
      dt = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')
    except ValueError as e:
      logger.error(f'Invalid time string: {time_str}. Error: {e}')
      raise
    if timezone:
      dt = dt.replace(tzinfo=ZoneInfo(timezone))
    return dt
