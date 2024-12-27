from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import plotly.graph_objs as go
from .helper.config import ContainerConfig
from .helper.utils import round_to_nearest_minute


class PlotManager:
  """
  Manages the creation and updating of plots for container data.

  Attributes
  ----------
  plot_cache : Dict[str, go.Layout]
      Cache for plot layouts to avoid recreating them.
  """

  def __init__(self):
    """
    Initializes the PlotManager with an empty plot cache.
    """
    self.plot_cache: Dict[str, go.Layout] = {}

  def create_combined_plot(
    self, data: Dict[str, List[Dict[str, Any]]], config: ContainerConfig
  ) -> go.Figure:
    """
    Creates a combined plot of load profile and consumption data for a container.

    Parameters
    ----------
    data : Dict[str, List[Dict[str, Any]]]
        Data to be plotted.
    config : ContainerConfig
        Configuration of the container.

    Returns
    -------
    go.Figure
        Plotly figure object containing the combined plot.
    """
    fig = self._get_or_create_figure(config)
    fig.data = []  # Clear existing traces

    self._add_load_profile_trace(fig, data.get('load_profile', []))
    self._add_consumption_trace(fig, data.get('consumption', []))

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
      return go.Figure(layout=self.plot_cache[config.container_name])

    fig = self._create_new_plot_layout(config)
    self.plot_cache[config.container_name] = fig.layout
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
        height=400,
      )
    )

  def _add_load_profile_trace(
    self, fig: go.Figure, load_profile_data: List[Dict[str, Any]]
  ) -> None:
    """
    Adds load profile trace to the figure.

    Parameters
    ----------
    fig : go.Figure
        Plotly figure object.
    load_profile_data : List[Dict[str, Any]]
        Load profile data to be plotted.

    Returns
    -------
    None
    """
    if not load_profile_data:
      return

    times, values = self._process_load_profile_data_points(load_profile_data)
    if times and values:
      fig.add_trace(
        go.Scatter(
          x=times,
          y=values,
          mode='lines+markers',
          name='Load Profile',
          line=dict(color='rgba(24, 115, 250, 0.6)'),
          marker=dict(size=8, color='rgba(24, 115, 250, 1.0)'),
          fill='tozeroy',
          fillcolor='rgba(24, 115, 250, 0.2)',
        )
      )

  def _process_load_profile_data_points(
    self, load_profile_data: List[Dict[str, Any]]
  ) -> Tuple[List[datetime], List[float]]:
    """
    Processes load profile data points and returns sorted times and values.

    Parameters
    ----------
    load_profile_data : List[Dict[str, Any]]
        Load profile data points.

    Returns
    -------
    Tuple[List[datetime], List[float]]
        Sorted times and values from the load profile data.
    """
    times = []
    values = []

    for entry in load_profile_data:
      timestamp = entry.get('timestamp')
      value = entry.get('value')
      if timestamp and value:
        times.append(self.parse_time_to_datetime(timestamp))
        values.append(value)

    if times and values:
      return zip(*sorted(zip(times, values)))
    return [], []

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
    dt = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')
    if timezone:
      from zoneinfo import ZoneInfo

      dt = dt.replace(tzinfo=ZoneInfo(timezone))
    return dt

  def _add_consumption_trace(
    self, fig: go.Figure, consumption_data: List[Dict[str, Any]]
  ) -> None:
    """
    Adds consumption trace to the figure.

    Parameters
    ----------
    fig : go.Figure
        Plotly figure object.
    consumption_data : List[Dict[str, Any]]
        Consumption data to be plotted.

    Returns
    -------
    None
    """
    if not consumption_data:
      return

    times, values = self._process_consumption_data_points(consumption_data)
    if times and values:
      fig.add_trace(
        go.Scatter(
          x=times,
          y=values,
          mode='lines+markers',
          name='Consumption',
          line=dict(color='rgba(250, 115, 24, 0.6)'),
          marker=dict(size=4, color='rgba(250, 115, 24, 1.0)'),
          fill='tozeroy',
          fillcolor='rgba(250, 115, 24, 0.2)',
        )
      )

  @staticmethod
  def _process_consumption_data_points(
    consumption_data: List[Dict[str, Any]],
  ) -> Tuple[List[datetime], List[float]]:
    """
    Processes consumption data points and returns sorted times and values.

    Parameters
    ----------
    consumption_data : List[Dict[str, Any]]
        Consumption data points.

    Returns
    -------
    Tuple[List[datetime], List[float]]
        Sorted times and values from the consumption data.
    """
    times = []
    values = []

    for entry in consumption_data:
      timestamp = entry.get('timestamp')
      value = entry.get('value')
      if timestamp and value:
        try:
          time = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')
        except ValueError:
          time = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S')
        times.append(round_to_nearest_minute(time))
        values.append(value)

    if not times or not values:
      return [], []

    # Sort by timestamp
    sorted_indices = sorted(range(len(times)), key=lambda i: times[i])
    return [times[i] for i in sorted_indices], [values[i] for i in sorted_indices]
