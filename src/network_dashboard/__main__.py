import os

from src.network_dashboard.dashboard import NetworkDashboard

if __name__ == '__main__':
  gradio_node_dashboard = NetworkDashboard(
    os.getenv('NODE_CONFIG_FILE', './development/env/env_variables.json')
  )
  interface = gradio_node_dashboard.create_interface()
  interface.launch(
    share=False,
    server_port=int(os.getenv('NODE_GRADIO_PORT', 7862)),
    server_name='0.0.0.0',
  )
