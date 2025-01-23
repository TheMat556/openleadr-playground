from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

import gradio as gr
import pandas as pd
import plotly.graph_objs as go
import math
import logging

from gradio import Timer

import requests
from dataclasses import dataclass
from typing import Optional, Dict, Any
import threading
import time

MINUTES_INTERVAL = 15
KWH_UNIT = 'kWh'
SLIDER_VALUE = 'Slider Value'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConsumptionData:
  timestamp: int
  total_consumption: float
  unit: str
  ven_count: int
  statistics: Dict[str, Any]


class ConsumptionService:
  """Service to handle consumption data retrieval"""

  def __init__(self, base_url: str = 'http://127.0.0.1:5000'):
    self.base_url = base_url
    self._last_consumption = 0.0
    self._lock = threading.Lock()

  def get_consumption_summary(self) -> Optional[ConsumptionData]:
    """Fetch consumption summary from the REST endpoint"""
    try:
      response = requests.get(f'{self.base_url}/api/consumption/summary')
      response.raise_for_status()
      data = response.json()

      with self._lock:
        self._last_consumption = data['total_consumption']

      return ConsumptionData(
        timestamp=data['timestamp'],
        total_consumption=data['total_consumption'],
        unit=data['unit'],
        ven_count=data['ven_count'],
        statistics=data['statistics'],
      )
    except Exception as e:
      logger.error(f'Failed to fetch consumption data: {e}')
      return None

  @property
  def current_consumption(self) -> float:
    """Get the last known consumption value"""
    with self._lock:
      return self._last_consumption


class AsyncGradioApp:
  TIMEZONE = timezone(timedelta(hours=1))
  """
  A Gradio application for interactive slider-based load profile visualization.

  This class creates a web interface with multiple sliders representing hourly load values,
  with real-time chart updates and the ability to save and interpolate slider values.

  :param num_sliders: Number of sliders to create in the interface, defaults to 24
  :type num_sliders: int, optional
  :param slider_file: Path to the file for storing and loading slider values, defaults to './slider_values.txt'
  :type slider_file: str, optional
  """

  def __init__(
    self,
    num_sliders: int = 24,
    slider_file: str = './slider_values.txt',
    consumption_service: Optional[ConsumptionService] = None,
  ) -> None:
    """
    Initialize the AsyncGradioApp.

    :param num_sliders: Number of sliders to create in the interface.
    :type num_sliders: int
    :param slider_file: Path to the file for storing and loading slider values.
    :type slider_file: str
    """
    super().__init__()
    self.num_sliders = num_sliders
    self.slider_file = slider_file
    self.slider_values = self.load_slider_values(slider_file)
    self.consumption_service = consumption_service or ConsumptionService()
    self._consumption_update_thread = None
    self.save_slider_values(*self.slider_values)
    self.start_consumption_updates()

  def start_consumption_updates(self):
    """Start background thread for consumption updates"""

    def update_loop():
      while True:
        self.consumption_service.get_consumption_summary()
        time.sleep(5)  # Update every 5 seconds

    self._consumption_update_thread = threading.Thread(target=update_loop, daemon=True)
    self._consumption_update_thread.start()

  def _on_update_consumption_data(self, sender: str, signal: str, data: float) -> None:
    """
    Update current consumption and refresh the label if it exists.

    :param sender: Signal sender.
    :type sender: str
    :param data: Consumption data dictionary.
    :type data: float
    """
    self._current_consumption = data

  def log_slider_file_issue(self, message: str) -> None:
    logger.warning(f'{message} Please create {self.slider_file} with integer values.')

  def load_slider_values(self, filename: str) -> List[int]:
    """
    Load slider values from a file or generate default values.

    :param filename: Path to the file containing slider values.
    :type filename: str
    :return: List of slider values, padded with default values if necessary.
    :rtype: list[int]
    """
    try:
      base_path = Path(__file__).parent.parent.parent
      filepath = (base_path / filename).resolve()
      with filepath.open('r') as file:
        values = [int(line.strip()) for line in file.readlines()]
      return values[: self.num_sliders] + [30] * (self.num_sliders - len(values))
    except FileNotFoundError:
      self.log_slider_file_issue(
        f'Slider values file not found at {filename}. Using default values.'
      )
      return [30] * self.num_sliders
    except ValueError as e:
      self.log_slider_file_issue(f'Invalid data in {filename}: {e}')
      return [30] * self.num_sliders

  def get_unix_timestamp_range(self) -> tuple:
    """
    Get start and end Unix timestamps for the current day in milliseconds.

    :return: Tuple of start and end Unix timestamps in milliseconds
    :rtype: tuple
    """
    now = datetime.now(self.TIMEZONE)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    return int(start_of_day.timestamp() * 1000), int(end_of_day.timestamp() * 1000)

  def datetime_to_unix_ms(self, dt: datetime) -> int:
    """
    Convert datetime to Unix timestamp in milliseconds.

    :param dt: datetime object
    :type dt: datetime
    :return: Unix timestamp in milliseconds
    :rtype: int
    """
    if dt.tzinfo is None:
      dt = dt.replace(tzinfo=self.TIMEZONE)
    return int(dt.timestamp() * 1000)

  def interpolate_slider_values(self, slider_values: List[int]) -> pd.DataFrame:
    """
    Interpolate slider values to create a 15-minute resolution time series with Unix timestamps in milliseconds (GMT+1).

    :param slider_values: List of hourly slider values
    :type slider_values: list[int]
    :return: Interpolated DataFrame with 15-minute resolution
    :rtype: pandas.DataFrame
    """
    start_timestamp, _end_timestamp = self.get_unix_timestamp_range()
    start_dt = datetime.fromtimestamp(start_timestamp / 1000).replace(
      tzinfo=self.TIMEZONE
    )

    time_index = pd.date_range(
      start=start_dt, periods=96, freq='15min', tz=self.TIMEZONE
    )
    original_time_index = pd.date_range(
      start=start_dt, periods=24, freq='1h', tz=self.TIMEZONE
    )

    df_original = pd.DataFrame(
      {'Time': original_time_index, SLIDER_VALUE: slider_values}
    )
    df_original.set_index('Time', inplace=True)

    df_interpolated = df_original.reindex(time_index).interpolate(method='linear')
    df_interpolated['unix_timestamp'] = df_interpolated.index.view('int64') // 10**6
    df_interpolated['display_time'] = df_interpolated.index.strftime('%H:%M')

    return df_interpolated[[SLIDER_VALUE, 'unix_timestamp', 'display_time']]

  def save_slider_values(self, *args: int) -> None:
    """
    Save slider values and generate interpolated load profile.

    Args:
        *args: Variable number of slider values
    """
    slider_values = list(args)[: self.num_sliders]
    self.slider_values = slider_values

    try:
      with open(self.slider_file, 'w') as file:
        for value in slider_values:
          file.write(f'{value}\n')
    except Exception as e:
      logger.error(f'Error saving slider values: {e}')

    # Get interpolated values and send directly to the next function
    interpolated_values = self.interpolate_slider_values(slider_values)
    self._send_interpolated_values(interpolated_values)

  def _send_interpolated_values(self, interpolated_values: pd.DataFrame) -> List[dict]:
    """
    Send interpolated slider values as load profile data.

    Args:
        interpolated_values: DataFrame containing interpolated values with unix_timestamp column

    Returns:
        List of intervals with dtstart, duration, and signal_payload
    """
    intervals = []
    for _, row in interpolated_values.iterrows():
      dt = datetime.fromtimestamp(int(row['unix_timestamp']) / 1000, timezone.utc)
      interval = {
        'dtstart': dt,
        'duration': timedelta(minutes=15),
        'signal_payload': row[SLIDER_VALUE],
      }
      intervals.append(interval)
    return intervals

  def get_current_allowed_consumption(self) -> str:
    """
    Get the current allowed consumption based on the interpolated slider values.

    :return: Current allowed consumption in kWh
    :rtype: str
    """
    interpolated_values = self.interpolate_slider_values(self.slider_values)
    now = datetime.now(timezone.utc)
    current_unix = self.datetime_to_unix_ms(now)

    # Find the closest 15-minute interval
    closest_row = interpolated_values.iloc[
      (interpolated_values['unix_timestamp'] - current_unix).abs().argsort()[:1]
    ]

    allowed_consumption = closest_row[SLIDER_VALUE].iloc[0]
    return f'{allowed_consumption} {KWH_UNIT}'

  def update_chart(self, *args: int) -> go.Figure:
    """
    Create a Plotly scatter plot visualization of slider values.

    :param args: Variable number of slider values.
    :type args: list[int]
    :return: Plotly Figure object with slider values visualization.
    :rtype: plotly.graph_objs._figure.Figure
    """
    slider_values = list(args)[: self.num_sliders]

    if not slider_values:
      slider_values = self.slider_values

    fig = go.Figure(
      data=[
        go.Scatter(
          x=[i for i in range(self.num_sliders)],
          y=list(slider_values),
          mode='lines+markers',
          line=dict(color='rgba(250, 115, 24, 0.6)'),
          marker=dict(size=8, color='rgba(250, 115, 24, 1.0)'),
        )
      ]
    )

    fig.update_layout(
      title={'text': 'Slider Values Visualization', 'font': {'color': 'white'}},
      xaxis_title='Data Points',
      yaxis_title=SLIDER_VALUE,
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

  def get_current_consumption(self) -> str:
    """
    Get the current consumption.

    :return: Current consumption in kWh
    :rtype: str
    """
    return f'{self.consumption_service.current_consumption} {KWH_UNIT}'

  def create_interface(self) -> gr.Blocks:
    """
    Create the Gradio interface with sliders and interactive plot.

    :return: Gradio Blocks interface.
    :rtype: gradio.Blocks
    """

    def create_slider(index):
      if index < self.num_sliders:
        return gr.Slider(
          minimum=0,
          maximum=30,
          value=self.slider_values[index],
          step=1,
          label=f'Slider {index}:00',
          scale=1,
        )
      else:
        return gr.Slider(visible=False)

    def create_slider_rows():
      rows = math.ceil(self.num_sliders / 4)
      slider_rows = []
      for i in range(rows):
        row_sliders = [create_slider(i * 4 + j) for j in range(4)]
        slider_rows.append(row_sliders)
      return slider_rows

    slider_rows = create_slider_rows()
    initial_plot = self.update_chart()

    with gr.Blocks(css='.gradio-container { max-width: 95% !important; }') as interface:
      with gr.Column():
        for row in slider_rows:
          with gr.Row():
            for slider in row:
              slider.render()

        plot_output = gr.Plot(value=initial_plot)
        inputs = [slider for row in slider_rows for slider in row if slider.visible]

        for row in slider_rows:
          for slider in row:
            if slider.visible:
              slider.change(
                fn=self.update_chart,
                inputs=inputs,
                outputs=plot_output,
              )
              slider.release(
                fn=self.save_slider_values,
                inputs=inputs,
              )

        with gr.Row():
          gr.Label(
            value=self.get_current_consumption, label='Node consumption', every=Timer(5)
          )
          gr.Label(
            value=self.get_current_allowed_consumption,
            label='Current allowed consumption',
            every=Timer(5),
          )

    return interface
