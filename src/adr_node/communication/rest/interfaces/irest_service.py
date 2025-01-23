from abc import ABC, abstractmethod

from src.adr_node.core.interfaces.irunable import IRunnable


class IRestService(ABC, IRunnable):
  @abstractmethod
  def start(self) -> None:
    pass

  @abstractmethod
  def stop(self) -> None:
    pass
