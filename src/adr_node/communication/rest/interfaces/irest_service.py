from abc import ABC, abstractmethod


class IRestService(ABC):
  @abstractmethod
  def start(self) -> None:
    pass

  @abstractmethod
  def stop(self) -> None:
    pass
