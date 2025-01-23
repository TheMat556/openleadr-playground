# main.py
from src.adr_node.mock_node_dashboard.config.app_config import AppConfig
from src.adr_node.mock_node_dashboard.dependency_injection.container import Container


def main():
  config = AppConfig(
    slider_file_path='./slider_values.txt',
    api_base_url='http://127.0.0.1:5000',
    num_sliders=24,
  )

  container = Container()
  container.config.from_dict(config.__dict__)

  app = container.gradio_app()
  interface = app.create_interface()
  interface.launch()


if __name__ == '__main__':
  main()
