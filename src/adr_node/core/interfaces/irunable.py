from abc import abstractmethod
from dataclasses import dataclass


@dataclass
class IRunnable:
  """
  Interface for runnable services.

  This interface defines the method that must be implemented by any
  runnable service class.
  """

  @abstractmethod
  def run(self) -> None:
    """
    Run the service.

    This method should contain the logic to run the service.
    """
    pass
