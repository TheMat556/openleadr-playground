from abc import ABC, abstractmethod

from src.adr_node.core.interfaces.irunable import IRunnable


class IRestService(ABC, IRunnable):
  """
  Interface for REST services.

  This interface defines the contract for REST services, including the
  methods that must be implemented by any class that inherits from it.
  """

  @abstractmethod
  def stop(self) -> None:
    """
    Stops the REST service.

    This method should be implemented to handle the logic required to
    stop the REST service.
    """
    pass
