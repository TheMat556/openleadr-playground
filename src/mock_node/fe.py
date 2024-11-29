import gradio as gr

from src import dispatcher


class SimpleGradioApp:
  def __init__(self):
    self.slider_value = 5
    self.text_value = "Hello, Gradio!"

  # Define the function that will be used in the interface
  def update_output(self, slider_value, text_value):
    self.slider_value = slider_value
    self.text_value = text_value
    return f"Slider Value: {slider_value}", f"Text Input: {text_value}"

  def launch_interface(self):
    # Define Gradio components
    slider = gr.Slider(minimum=0, maximum=10, step=1, value=self.slider_value, label="Adjust the slider")
    text_input = gr.Textbox(value=self.text_value, label="Enter some text")

    # Create Gradio interface
    interface = gr.Interface(
      fn=self.update_output,  # Function to call on input change
      inputs=[slider, text_input],  # Inputs (slider and textbox)
      outputs=[gr.Textbox(), gr.Textbox()],  # Outputs (two textboxes for displaying results)
      live=True  # Enable live update
    )

    # Launch the interface
    interface.launch()

if __name__ == '__main__':
  print(id(dispatcher))
  # Instantiate and launch the app
  app = SimpleGradioApp()
  app.launch_interface()
