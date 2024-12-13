import os
from multiprocessing import Process

from dotenv import load_dotenv

from development_configs.simple.node_runner import (
  run_mock_node,
  run_house_node,
  run_gradio,
  run_node_dashboard,
)

if __name__ == '__main__':
  load_dotenv(dotenv_path='./development_configs/simple/.env')
  print(os.getenv('DEV_VTN_NAME'))

  process_mock_node = Process(target=run_mock_node)
  process_house_node = Process(target=run_house_node)
  proces_gradio = Process(target=run_gradio)
  proces_node_dashboard = Process(target=run_node_dashboard)

  process_mock_node.start()
  process_house_node.start()
  proces_gradio.start()
  proces_node_dashboard.start()

  process_mock_node.join()
  process_house_node.join()
  proces_gradio.join()
  proces_node_dashboard.join()
