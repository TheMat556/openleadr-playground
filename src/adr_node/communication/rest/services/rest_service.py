from flask import Flask
import threading
from datetime import datetime, timezone

from src.adr_node.communication.rest.exceptions.service_shutdown_error import (
  ServiceShutdownError,
)
from src.adr_node.communication.rest.exceptions.service_startup_error import (
  ServiceStartupError,
)
from src.adr_node.communication.rest.interfaces.irest_service import IRestService
from src.adr_node.communication.rest.routes.handlers.consumption_handler import (
  ConsumptionHandler,
)
from src.adr_node.communication.rest.routes.handlers.load_profile_handler import (
  LoadProfileHandler,
)
from src.adr_node.communication.rest.routes.handlers.status_handler import StatusHandler
from src.adr_node.database.services.core.consumption_service import ConsumptionService
from src.adr_node.database.services.core.load_profile_service import LoadProfileService
import logging


class RestService(IRestService):
  """
  REST service for handling API requests.

  This class initializes and manages the Flask application, registers routes,
  and handles the startup and shutdown of the service.
  """

  version = '0.0.1'
  startup_time = datetime.now(timezone.utc)

  def __init__(
    self,
    host: str,
    port: int,
    load_profile_service: LoadProfileService,
    consumption_service: ConsumptionService,
  ):
    """
    Initialize the REST service.

    Parameters
    ----------
    host : str
        The host address for the Flask application.
    port : int
        The port number for the Flask application.
    load_profile_service : LoadProfileService
        The service for handling load profile data.
    consumption_service : ConsumptionService
        The service for handling consumption data.
    """
    self._host = host
    self._port = port
    self._app = Flask(__name__)
    self._server = None

    # Initialize handlers
    self._handlers = [
      StatusHandler(),
      ConsumptionHandler(consumption_service),
      LoadProfileHandler(load_profile_service),
    ]

    self._register_routes()

  def _register_routes(self):
    """Register all routes from handlers."""
    for handler in self._handlers:
      for method_name in dir(handler):
        method = getattr(handler, method_name)
        if hasattr(method, '_endpoint'):
          self._app.add_url_rule(
            method._endpoint, view_func=method, methods=method._methods
          )

  def start(self) -> None:
    """
    Start the REST service.

    This method starts the Flask application in a separate thread.
    """
    try:
      self._server = threading.Thread(
        target=self._app.run, kwargs={'host': '0.0.0.0', 'port': self._port}
      )
      self._server.daemon = True
      self._server.start()
      logging.info(f'REST service started on {self._host}:{self._port}')
    except Exception as e:
      error_msg = f'Failed to start REST service: {str(e)}'
      logging.error(error_msg)
      raise ServiceStartupError(error_msg)

  def stop(self) -> None:
    """
    Stop the REST service.

    This method stops the Flask application.
    """
    try:
      if self._server and self._server.is_alive():
        # Implement proper Flask shutdown
        pass
    except Exception as e:
      raise ServiceShutdownError(f'Failed to stop REST service: {str(e)}')

  def run(self):
    """Run the REST service."""
    self.start()
