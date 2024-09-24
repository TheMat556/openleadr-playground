import asyncio
import os
import threading
from pathlib import Path
from dotenv import load_dotenv

from src.client import OpenLeADRClient
from src.live_charting import LiveCharting, DataGenerator
from src.server import OpenLeADRServer

current_path = Path.cwd()
shutdown_event = threading.Event()


def get_leadr_server():
    return OpenLeADRServer(os.getenv("SERVER_NAME"), os.getenv("DB_NAME"))


def get_leadr_client():
    return OpenLeADRClient(os.getenv("VEN_NAME"), os.getenv("VTN_URL"))


def get_dash_app():
    return LiveCharting("./src/database/dummy_data_db", "dummy_data_table")


def get_data_generator():
    return DataGenerator("./src/database/dummy_data_db", "dummy_data_table")


def run_dash_app():
    dash = get_dash_app()
    dash.app.run_server(debug=True, use_reloader=False)


async def main():
    load_dotenv()

    open_leadr_server = get_leadr_server()
    open_leadr_client = get_leadr_client()

    # Start the Dash app in a separate thread
    threading.Thread(target=run_dash_app, daemon=True).start()

    # Run your asyncio tasks here
    await asyncio.gather(
        open_leadr_server.server.run(),
        open_leadr_client.client.run(),
        get_data_generator().generate_interval_data(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
