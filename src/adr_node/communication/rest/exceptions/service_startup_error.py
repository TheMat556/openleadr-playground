from src.adr_node.communication.rest.exceptions.rest_service_exception import (
  RestServiceException,
)


class ServiceStartupError(RestServiceException):
  """
  Raised when the service fails to start.

  This exception is used to indicate that the service encountered an error
  during the startup process.
  """

  pass
