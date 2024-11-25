import streamlit as st
import pandas as pd
import streamlit_vertical_slider as svs
import altair as alt
import numpy as np


class MockNodeUI:
  def __init__(self, file_path):
    self.file_path = file_path
    self.hours = [i for i in range(0, 25)]
    self.values = self.read_values()
    self.sliders = {}

  def read_values(self):
    try:
      with open(self.file_path, 'r') as f:
        return [int(val.strip()) for val in f.readlines()]
    except FileNotFoundError:
      return [0] * 25

  def save_values(self):
    with open(self.file_path, 'w') as f:
      f.writelines(f'{val}\n' for val in self.values)

  def generate_15_min_values(self):
    intervals = np.linspace(0, 24, 97)
    hour_intervals = np.arange(25)
    interpolated_values = np.interp(intervals, hour_intervals, self.values)

    times = [
      f'{int(interval):02d}:{int((interval % 1) * 60):02d}' for interval in intervals
    ]
    df_15_min = pd.DataFrame({'Time': times, 'Values': interpolated_values})
    print(df_15_min.tail(15))
    return df_15_min

  def render_sliders(self):
    st.header('Lastprofil')
    columns = st.columns(len(self.hours))

    for idx, hour in enumerate(self.hours):
      key = f'slider_{hour}'
      with columns[idx]:
        st.markdown(
          f"<div style='text-align: center; font-size: 10px; color: gray;'>{hour}:00</div>",
          unsafe_allow_html=True,
        )
        self.sliders[key] = svs.vertical_slider(
          key=key, default_value=self.values[idx], step=1, min_value=0, max_value=30
        )
        self.values[idx] = self.sliders[key]

    self.save_values()
    self.generate_15_min_values()

  def render_chart(self):
    df = pd.DataFrame({'hours': self.hours, 'Values': self.values})
    df['Type'] = 'project'
    chart = (
      alt.Chart(df)
      .mark_line(color='red', interpolate='cardinal')
      .encode(
        x=alt.X('hours', axis=alt.Axis(title='hours'), scale=alt.Scale(domain=[0, 24])),
        y=alt.Y('Values', axis=alt.Axis(title='Values')),
        tooltip=['hours', alt.Tooltip('Values')],
      )
    )
    st.altair_chart(chart, use_container_width=True)

  def render_metrics(self):
    st.header('Messungen')
    col1, col2, col3 = st.columns(3)
    col1.metric('Temperature', '70 °F', '1.2 °F')
    col2.metric('Wind', '9 mph', '-8%')
    col3.metric('Humidity', '86%', '4%')

  def run(self):
    self.render_sliders()
    self.render_chart()
    self.render_metrics()  #


if __name__ == '__main__':
  st.set_page_config(page_title='Mock Node UI', layout='wide')
  app = MockNodeUI(file_path='slider_values.txt')
  app.run()
