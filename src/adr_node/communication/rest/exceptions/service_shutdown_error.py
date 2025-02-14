from src.adr_node.communication.rest.exceptions.rest_service_exception import (
  RestServiceException,
)


class ServiceShutdownError(RestServiceException):
  """
  Raised when the service fails to shutdown.

  This exception is used to indicate that the service encountered an error
  during the shutdown process.
  """

  pass
