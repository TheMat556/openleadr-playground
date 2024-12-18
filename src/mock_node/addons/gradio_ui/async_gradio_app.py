import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

import gradio as gr
import pandas as pd
import plotly.graph_objs as go
import math

from gradio import Timer
import logging

from src.openadr_node.adr_base_config import AdrBaseConfig
from src.openadr_node.decorator.signal_connector import SignalConnector
from src.openadr_node.decorator.signal_sender import SignalSender

MINUTES_INTERVAL = 15
KWH_UNIT = 'kWh'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SLIDER_VALUE = 'Slider Value'


class AsyncGradioApp(AdrBaseConfig):
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
    self, num_sliders: int = 24, slider_file: str = './slider_values.txt'
  ) -> None:
    super().__init__()
    self.num_sliders = num_sliders
    self.slider_file = slider_file
    self.slider_values = self.load_slider_values(slider_file)
    self._current_consumption = 0
    self.save_slider_values(*self.slider_values)  # Send interpolated values at startup

  @SignalConnector('update_consumption_data', 'nm')
  def _on_update_consumption_data(self, sender: str, signal: str, data: float) -> None:
    """
    Update current consumption and refresh the label if it exists.

    :param sender: Signal sender
    :param data: Consumption data dictionary
    """
    self._current_consumption = data

  def load_slider_values(self, filename: str) -> List[int]:
    """
    Load slider values from a file or generate default values.

    :param filename: Path to the file containing slider values
    :type filename: str
    :return: List of slider values, padded with default values if necessary
    :rtype: list[int]
    """
    try:
      base_path = Path(__file__).parent.parent.parent
      print('BASE PATH:', base_path)
      filepath = (base_path / filename).resolve()

      with filepath.open('r') as file:
        values = [int(line.strip()) for line in file.readlines()]
      return values[: self.num_sliders] + [30] * (self.num_sliders - len(values))
    except FileNotFoundError:
      logging.warning(
        f'Slider values file not found at {filename}. Using default values.'
      )
      return [30] * self.num_sliders
    except ValueError as e:
      logging.error(f'Invalid data in {filename}: {e}')
      return [30] * self.num_sliders

  def interpolate_slider_values(self, slider_values: List[int]) -> pd.DataFrame:
    """
    Interpolate slider values to create a 15-minute resolution time series.

    :param slider_values: List of hourly slider values
    :type slider_values: list[int]
    :return: Interpolated DataFrame with 15-minute resolution time index
    :rtype: pandas.DataFrame
    """
    time_index = pd.date_range(start='2024-01-01 00:00:00', periods=96, freq='15min')
    original_time_index = pd.date_range(
      start='2024-01-01 00:00:00', periods=24, freq='1h'
    )

    df_original = pd.DataFrame(
      {'Time': original_time_index, SLIDER_VALUE: slider_values}
    )

    df_original.set_index('Time', inplace=True)
    df_interpolated = df_original.reindex(time_index).interpolate(method='linear')
    df_interpolated.index = df_interpolated.index.strftime('%H:%M')

    return df_interpolated[[SLIDER_VALUE]]

  def save_slider_values(self, *args: int) -> None:
    """
    Save slider values to a file and send interpolated values via dispatcher.

    :param args: Variable number of slider values
    :type args: list[int]
    """
    slider_values = list(args)[: self.num_sliders]
    self.slider_values = slider_values

    try:
      with open(self.slider_file, 'w') as file:
        for value in slider_values:
          file.write(f'{value}\n')
    except Exception as e:
      print(f'Error saving slider values: {e}')

    interpolated_values = self.interpolate_slider_values(slider_values)

    result = {
      f'timestamp_{i}': {'time': index, 'value': row['Slider Value']}
      for i, (index, row) in enumerate(interpolated_values.iterrows())
    }

    json_result = json.dumps(result, indent=None, separators=(',', ':'))

    self._send_interpolated_values(json_result)

  @SignalSender('update_load_profile', 'ui')
  def _send_interpolated_values(self, value: str) -> List[dict]:
    data = json.loads(value)
    intervals = []
    start_time = datetime.now().replace(
      hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
    )
    for key, val in data.items():
      time_str = val['time']
      hours, minutes = map(int, time_str.split(':'))
      dtstart = start_time + timedelta(hours=hours, minutes=minutes)
      interval = {
        'dtstart': dtstart,
        'duration': timedelta(minutes=15),
        'signal_payload': val['value'],
      }
      intervals.append(interval)
    return intervals

  def update_chart(self, *args: int) -> go.Figure:
    """
    Create a Plotly scatter plot visualization of slider values.

    :param args: Variable number of slider values
    :type args: list[int]
    :return: Plotly Figure object with slider values visualization
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

  def create_interface(self) -> gr.Blocks:
    """
    Create the Gradio interface with sliders and interactive plot.
    :return: Gradio Blocks interface
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
          scale=1,  # Distribute space equally
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

  def get_current_consumption(self) -> str:
    return f'{self._current_consumption} {KWH_UNIT}'

  def get_current_allowed_consumption(self) -> str:
    interpolated_values = self.interpolate_slider_values(self.slider_values)
    now = datetime.now()
    minutes = (now.minute // MINUTES_INTERVAL) * MINUTES_INTERVAL
    rounded_time = now.replace(minute=minutes, second=0, microsecond=0)
    rounded_time_str = rounded_time.strftime('%H:%M')
    allowed_consumption = interpolated_values.loc[rounded_time_str, SLIDER_VALUE]

    return f'{allowed_consumption} {KWH_UNIT}'


def main() -> None:
  """
  Main function to create and launch the AsyncGradioApp.
  """
  app = AsyncGradioApp(num_sliders=24, slider_file='slider_values.txt')
  interface = app.create_interface()
  interface.launch(share=True)


if __name__ == '__main__':
  main()
