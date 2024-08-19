# src/client/__main__.py
import asyncio
import logging

from .openleadr_client import OpenLeADRClient

logger = logging.getLogger(__name__)

def main():
    """
    Main entry point to initialize and run the OpenLeADR client.
    """

    ven_name = "ven123"
    vtn_url = "http://localhost:8080/OpenADR2/Simple/2.0b"
    open_leadr_client = OpenLeADRClient(ven_name=ven_name, vtn_url=vtn_url)

    try:
        loop = asyncio.new_event_loop()
        loop.create_task(open_leadr_client.client.run())
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Client interrupted by user.")
    finally:
        logger.info("Client stopped.")

if __name__ == "__main__":
    main()
