import asyncio
import os

from dotenv import load_dotenv

from src.openadr_node.node_manager import NodeManager


async def run_node_frontend():
  current_dir = os.getcwd()
  script_path = os.path.join(current_dir, 'addons\streamlit.py')

  process = await asyncio.create_subprocess_exec('streamlit', 'run', script_path)

  await process.wait()


def main():
  load_dotenv()

  node_manager = NodeManager(
    # vtn_name=os.getenv('SERVER_NAME'),
    ven_name=os.getenv('VEN_NAME'),
    vtn_url=os.getenv('VTN_URL'),
  )
  node_manager.add_task(run_node_frontend())
  node_manager.run_node()
  pass


if __name__ == '__main__':
  main()
