from abc import abstractmethod, ABC


class IComponentController(ABC):
  @abstractmethod
  def start(self) -> None:
    pass

  @abstractmethod
  def stop(self) -> None:
    pass
