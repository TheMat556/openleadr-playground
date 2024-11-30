from signal import signal

import gradio as gr
import pandas as pd
import plotly.graph_objs as go
import math
from pydispatch import dispatcher


class AsyncGradioApp:
  def __init__(self, num_sliders=24, slider_file='./slider_values.txt'):
    self.num_sliders = num_sliders
    self.slider_file = slider_file
    self.slider_values = self.load_slider_values(slider_file)
    print(dispatcher)

  def load_slider_values(self, filename):
    """Load slider values from a file."""
    try:
      with open(filename, 'r') as file:
        values = [float(line.strip()) for line in file.readlines()]
      return values[: self.num_sliders] + [30] * (self.num_sliders - len(values))
    except FileNotFoundError:
      print(f'{filename} not found. Using default values.')
      return [30] * self.num_sliders

  def interpolate_slider_values(self, slider_values):
    time_index = pd.date_range(start='2024-01-01 00:00:00', periods=96, freq='15T')
    original_time_index = pd.date_range(
      start='2024-01-01 00:00:00', periods=24, freq='1H'
    )

    df_original = pd.DataFrame(
      {'Time': original_time_index, 'Slider Value': slider_values}
    )

    df_original.set_index('Time', inplace=True)
    df_interpolated = df_original.reindex(time_index).interpolate(method='linear')
    df_interpolated.index = df_interpolated.index.strftime('%H:%M')

    return df_interpolated[['Slider Value']]

  def save_slider_values(self, slider_values):
    interpolated_values = self.interpolate_slider_values(slider_values)
    dispatcher.send(
      signal="update_load_profile",
      sender="UI",
      data=interpolated_values.to_json(),
    )
    try:
      with open(self.slider_file, 'w') as file:
        for value in slider_values:
          file.write(f'{value}\n')
    except Exception as e:
      print(f'Error saving slider values: {e}')

  def update_chart(self, *slider_values):
    if not slider_values:
      slider_values = self.slider_values

    self.save_slider_values(slider_values)

    fig = go.Figure(
      data=[
        go.Scatter(
          x=[i + 1 for i in range(self.num_sliders)],
          y=list(slider_values),
          mode='lines+markers',
          line=dict(color='rgba(250, 115, 24, 0.6)'),
          marker=dict(size=8, color='rgba(250, 115, 24, 1.0)'),
        )
      ]
    )

    # Customize the layout with transparent background and white font
    fig.update_layout(
      title={'text': 'Slider Values Visualization', 'font': {'color': 'white'}},
      xaxis_title='Data Points',
      yaxis_title='Slider Value',
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
      plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot background
      paper_bgcolor='rgba(0,0,0,0)',  # Transparent overall background
      font_color='white',  # Global font color
      template='plotly_dark',  # Dark template as base
    )

    return fig

  def create_interface(self):
    rows = math.ceil(self.num_sliders / 4)

    slider_rows = []
    for i in range(rows):
      row_sliders = []
      for j in range(4):
        slider_index = i * 4 + j
        if slider_index < self.num_sliders:
          row_sliders.append(
            gr.Slider(
              minimum=0,
              maximum=30,
              value=self.slider_values[slider_index],
              step=1,
              label=f'Slider {slider_index}:00',
              scale=1,  # Distribute space equally
            )
          )
        else:
          row_sliders.append(gr.Slider(visible=False))

      slider_rows.append(row_sliders)

    initial_plot = self.update_chart()

    with gr.Blocks(css='.gradio-container { max-width: 95% !important; }') as interface:
      with gr.Column():
        for row in slider_rows:
          with gr.Row():
            for slider in row:
              slider.render()

        plot_output = gr.Plot(value=initial_plot)

        inputs = [slider for row in slider_rows for slider in row if slider.visible]
        inputs = [slider for slider in inputs if slider is not None]

        for row in slider_rows:
          for slider in row:
            if slider.visible:
              slider.change(
                fn=self.update_chart,
                inputs=inputs,
                outputs=plot_output,
              )
        with gr.Row():
          gr.Label('25kWh', label='Node consumption')
          gr.Label('12KWh', label='Current allowed consumption')

    return interface


def main():
  # Create and launch the app with the specified slider file
  app = AsyncGradioApp(num_sliders=24, slider_file='slider_values.txt')
  app.create_interface().launch()


if __name__ == '__main__':
  main()
