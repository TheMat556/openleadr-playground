# src/server/__main__.py
import asyncio
import logging

from .openleadr_server import OpenLeADRServer

logger = logging.getLogger(__name__)
def main():
    """
    Main entry point to initialize and run the OpenLeADR server.
    """
    server_name = "openleadr-server"
    db_name = "./database/openleadr.db"
    open_leadr_server = OpenLeADRServer(server_name, db_name)

    try:
        loop = asyncio.new_event_loop()
        loop.create_task(open_leadr_server.server.run())
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user.")
    finally:
        open_leadr_server.db_conn.close()
        logger.info("Server stopped and database connection closed.")


if __name__ == "__main__":
    main()
