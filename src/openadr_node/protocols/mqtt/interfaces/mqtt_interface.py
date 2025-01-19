from abc import ABC, abstractmethod


class IMQTTController(ABC):
  @abstractmethod
  def start(self) -> None:
    pass

  @abstractmethod
  def stop(self) -> None:
    pass

  @abstractmethod
  def publish_load_profile(self) -> None:
    pass
