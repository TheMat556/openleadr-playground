from functools import wraps
from pydispatch import dispatcher
from typing import Callable, Optional, Any

from src.openadr_node import logger


class SignalConnector:
  """
  A decorator class for connecting signals using the pydispatch library.
  """

  def __init__(
    self, signal: Optional[str] = None, sender: Optional[str] = None
  ) -> None:
    """
    Initialize the ConnectDispatcher decorator.

    :param signal: Custom signal to use. If not provided, the method name will be used.
    :type signal: str, optional
    :param sender: Custom sender to use. Defaults to `None`.
    :type sender: str, optional
    """
    self._custom_signal = signal
    self._custom_sender = sender

  def decorate(self, func: Callable) -> Callable:
    """
    Decorate a method to connect it to a signal at runtime.

    :param func: The function to connect to the signal.
    :type func: Callable
    :return: The wrapped function.
    :rtype: Callable
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
      # Call the original method
      try:
        return func(*args, **kwargs)
      except Exception as e:
        logger.error(f'Error in signal handler {func.__name__}: {e}')
        raise e

    # Attach signal and sender information for connection later
    wrapper._signal = self._custom_signal or func.__name__
    wrapper._sender = self._custom_sender
    wrapper._original_func = func

    return wrapper

  def __call__(self, func: Callable) -> Callable:
    """
    Callable method for the decorator, delegates to `decorate`.

    :param func: The function to connect to the signal.
    :type func: Callable
    :return: The wrapped function.
    :rtype: Callable
    """
    return self.decorate(func)

  @classmethod
  def connect_all(cls, instance: Any) -> None:
    """
    Connect all decorated dispatcher methods for a given instance.

    :param instance: The instance of the class.
    :type instance: Any
    """
    for name, method in vars(instance.__class__).items():
      # Check if the method was decorated
      if hasattr(method, '_signal') and hasattr(method, '_original_func'):
        # Create a bound method for the instance
        bound_method = method.__get__(instance, instance.__class__)
        if not hasattr(instance, '_signal_connections'):
          instance._signal_connections = []
          instance._signal_connections.append(
            (bound_method, method._signal, method._sender)
          )

        # Connect the bound method to the dispatcher
        dispatcher.connect(
          receiver=bound_method, signal=method._signal, sender=method._sender
        )
        logger.info(
          f'Connected {name} to signal: {method._signal} with sender: {method._sender}'
        )

  @classmethod
  def disconnect_all(cls, instance: Any) -> None:
    """Disconnect all signals for cleanup"""
    if hasattr(instance, '_signal_connections'):
      for receiver, signal, sender in instance._signal_connections:
        dispatcher.disconnect(receiver, signal, sender)
      instance._signal_connections.clear()
