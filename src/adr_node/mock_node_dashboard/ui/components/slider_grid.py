import gradio as gr
from typing import List
import math


class SliderGrid:
  """
  Class to create and manage a grid of sliders.

  :param num_sliders: Number of sliders to create.
  :type num_sliders: int
  :param columns: Number of columns in the grid.
  :type columns: int
  :param min_value: Minimum value for sliders.
  :type min_value: int
  :param max_value: Maximum value for sliders.
  :type max_value: int
  :param default_value: Default value for sliders.
  :type default_value: int
  :param step: Step size for sliders.
  :type step: int
  """

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

    :param hour: Hour of the day (0-23).
    :type hour: int
    :return: Gradio Slider component.
    :rtype: gr.Slider
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

    :return: List of all created sliders.
    :rtype: List[gr.Slider]
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

    :return: List of current slider values.
    :rtype: List[int]
    """
    return [slider.value for slider in self._sliders]

  def set_values(self, values: List[int]) -> None:
    """
    Set values for all sliders.

    :param values: List of values to set.
    :type values: List[int]
    """
    for slider, value in zip(self._sliders, values):
      slider.value = value
