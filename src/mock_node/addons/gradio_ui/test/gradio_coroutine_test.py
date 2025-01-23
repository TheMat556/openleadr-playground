# just a simple test to check if the ui can run with asyncio in the event loop
import asyncio
import threading

import nest_asyncio

from src.mock_node.addons.gradio_ui.async_gradio_app import AsyncGradioApp


def run_gradio_thread(interface):
  """Run Gradio in a separate thread"""
  interface.launch(server_port=7861, server_name='127.0.0.1')


async def run_other_coroutines():
  """Simulated coroutines that need to run concurrently"""
  while True:
    print('Running VTN Server Coroutine...')
    await asyncio.sleep(2)


async def run_ven_coroutine():
  """Simulated VEN Server Coroutine"""
  while True:
    print('Running VEN Server Coroutine...')
    await asyncio.sleep(3)


async def main():
  # Enable nested asyncio support
  nest_asyncio.apply()

  # Instantiate the app
  app = AsyncGradioApp()

  # Create Gradio interface
  interface = app.create_interface()

  # Run Gradio in a separate thread
  gradio_thread = threading.Thread(
    target=run_gradio_thread, args=(interface,), daemon=True
  )
  gradio_thread.start()

  # Create tasks for other coroutines
  vtn_task = asyncio.create_task(run_other_coroutines())
  ven_task = asyncio.create_task(run_ven_coroutine())

  # Wait for coroutines
  await asyncio.gather(vtn_task, ven_task)


if __name__ == '__main__':
  # Run the async main function
  asyncio.run(main())
