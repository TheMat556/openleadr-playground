# src/ui/components/slider_grid.py
import gradio as gr
from typing import List
import math


class SliderGrid:
  def __init__(
    self,
    num_sliders: int = 24,
    columns: int = 4,
    min_value: int = 0,
    max_value: int = 30,
    default_value: int = 30,
    step: int = 1,
  ):
    self.num_sliders = num_sliders
    self.columns = columns
    self.min_value = min_value
    self.max_value = max_value
    self.default_value = default_value
    self.step = step
    self._sliders: List[gr.Slider] = []

  def create_slider(self, hour: int) -> gr.Slider:
    """
    Create a single slider component.

    Args:
        hour: Hour of the day (0-23)

    Returns:
        Gradio Slider component
    """
    return gr.Slider(
      minimum=self.min_value,
      maximum=self.max_value,
      value=self.default_value,
      step=self.step,
      label=f'{hour:02d}:00',
      scale=1,
    )

  def create(self) -> List[gr.Slider]:
    """
    Create the complete grid of sliders.

    Returns:
        List of all created sliders
    """
    rows = math.ceil(self.num_sliders / self.columns)
    self._sliders = []

    for row in range(rows):
      with gr.Row():
        for col in range(self.columns):
          slider_index = row * self.columns + col
          if slider_index < self.num_sliders:
            slider = self.create_slider(slider_index)
            self._sliders.append(slider)
          else:
            gr.Slider(visible=False)

    return self._sliders

  def get_values(self) -> List[int]:
    """
    Get current values from all sliders.

    Returns:
        List of current slider values
    """
    return [slider.value for slider in self._sliders]

  def set_values(self, values: List[int]) -> None:
    """
    Set values for all sliders.

    Args:
        values: List of values to set
    """
    for slider, value in zip(self._sliders, values):
      slider.value = value
