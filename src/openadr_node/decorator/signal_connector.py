from functools import wraps
from pydispatch import dispatcher

from src.openadr_node import logger


class SignalConnector:
  def __init__(self, signal=None, sender=None):
    """
    Initialize the ConnectDispatcher decorator.

    Args:
        signal (str, optional): Custom signal to use. If not provided, the method name will be used.
        sender (str, optional): Custom sender to use. Defaults to `None`.
    """
    self._custom_signal = signal
    self._custom_sender = sender

  def decorate(self, func):
    """
    Decorate a method to connect it to a signal at runtime.

    Args:
        func (callable): The function to connect to the signal.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
      # Call the original method
      return func(*args, **kwargs)

    # Attach signal and sender information for connection later
    wrapper._signal = self._custom_signal or func.__name__
    wrapper._sender = self._custom_sender
    wrapper._original_func = func

    return wrapper

  def __call__(self, func):
    """
    Callable method for the decorator, delegates to `decorate`.
    """
    return self.decorate(func)

  @classmethod
  def connect_all(cls, instance):
    """
    Connect all decorated dispatcher methods for a given instance.

    Args:
        instance: The instance of the class
    """
    for name, method in vars(instance.__class__).items():
      # Check if the method was decorated
      if hasattr(method, '_signal') and hasattr(method, '_original_func'):
        # Create a bound method for the instance
        bound_method = method.__get__(instance, instance.__class__)

        # Connect the bound method to the dispatcher

        dispatcher.connect(
          receiver=bound_method, signal=method._signal, sender=method._sender
        )
        # dispatcher.send(signal="register_dispatcher", sender=method._sender, data=method._signal)
        logger.info(
          f'Connected {name} to signal: {method._signal} with sender: {method._sender}'
        )
