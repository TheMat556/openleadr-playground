from abc import abstractmethod, ABC


class IComponentController(ABC):
  """
  Interface for component controllers.

  This interface defines the methods that must be implemented by any
  component controller class.
  """

  @abstractmethod
  def start(self) -> None:
    """
    Start the component.

    This method should contain the logic to start the component.
    """
    pass

  @abstractmethod
  def stop(self) -> None:
    """
    Stop the component.

    This method should contain the logic to stop the component.
    """
    pass
