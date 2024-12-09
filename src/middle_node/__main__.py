import os

from dotenv import load_dotenv

from src.openadr_node.node_manager import NodeManager

def main():

  load_dotenv()

  node_manager = NodeManager(
    vtn_name=os.getenv('VTN_NAME'), vtn_path_prefix=os.getenv('VTN_PATH_PREFIX')
  )

  node_manager.run_node()

if __name__ == '__main__':
  main()
