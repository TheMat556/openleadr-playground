import asyncio
import os

from dotenv import load_dotenv

from src.openadr_node.node_manager import NodeManager

from src.openadr_node.async_event_bus import dispatcher


async def run_node_frontend():
  """Run Streamlit frontend as a subprocess."""
  current_dir = os.getcwd()
  script_path = os.path.join(current_dir, 'fe.py')

  process = await asyncio.create_subprocess_exec('streamlit', 'run', script_path)
  await process.wait()


def main():
  """Main function to set up and run the node manager."""
  print(id(dispatcher))
  load_dotenv()

  node_manager = NodeManager(
    vtn_name=os.getenv('SERVER_NAME'),
    # ven_name=os.getenv('VEN_NAME'),
    # vtn_url=os.getenv('VTN_URL'),
  )
  node_manager.add_task(run_node_frontend)
  node_manager.run_node()


if __name__ == '__main__':
  main()
