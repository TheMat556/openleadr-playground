# src/server/__main__.py
import asyncio
import logging

from .live_charting import LiveCharting
from .dummy_db import DataGenerator

logger = logging.getLogger(__name__)


async def main():
    data_generator = DataGenerator()
    live_charting = LiveCharting()

    try:
        loop = asyncio.new_event_loop()
        await loop.create_task(live_charting.app.server.run())
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user.")
    finally:
        logger.info("Server stopped and database connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
