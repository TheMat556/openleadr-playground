from abc import ABC, abstractmethod


class IFlaskAppService(ABC):
  @abstractmethod
  def serve_forever(self) -> None:
    """Start the Flask server"""
    pass

  @abstractmethod
  def shutdown(self) -> None:
    """Shutdown the Flask server"""
    pass
