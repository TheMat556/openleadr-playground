import os

from src.node_dashboard.dashboard import GradioNodeDashboard

if __name__ == '__main__':
  gradio_node_dashboard = GradioNodeDashboard()
  interface = gradio_node_dashboard.create_interface()
  interface.launch(
    share=False,
    server_port=int(os.getenv('NODE_GRADIO_PORT', 7862)),
    server_name='0.0.0.0',
  )
