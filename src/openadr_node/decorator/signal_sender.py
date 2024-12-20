from functools import wraps
from pydispatch import dispatcher
import logging
from typing import Optional, Callable, Any, List, Tuple


class SignalSender:
  """
  A decorator class for sending signals using the pydispatch library.
  """

  def __init__(
    self, signal: Optional[str] = None, sender: Optional[str] = None
  ) -> None:
    """
    Initialize the SendDispatcher decorator.

    :param signal: Custom signal to use. If not provided, the method name will be used.
    :type signal: str, optional
    :param sender: Custom sender to use. Defaults to `None`.
    :type sender: str, optional
    """
    self._custom_signal = signal
    self._custom_sender = sender
    self._ready_dispatched = False
    self._queue: List[Tuple[Callable, Tuple[Any], dict]] = []

    dispatcher.connect(self.on_ready, signal='on_ready', sender=dispatcher.Any)

  def on_ready(self, sender: Any) -> None:
    """
    This method is called when the "on_ready" event is dispatched.
    It will enable the dispatching of the `register_dispatcher` event.

    :param sender: The sender of the signal.
    :type sender: Any
    """
    logging.info('on_ready event received. Ready to register dispatchers.')
    if not self._ready_dispatched:
      dispatcher.send(
        signal='register_dispatcher',
        sender=self._custom_sender,
        data=self._custom_signal,
      )
      logging.info(
        f"Dispatched 'register_dispatcher' signal from {self._custom_sender}"
      )
      self._ready_dispatched = True

      while self._queue:
        func, args, kwargs = self._queue.pop(0)
        func(*args, **kwargs)

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
      if not self._ready_dispatched:
        logging.warning(
          'on_ready event has not been dispatched. Queuing function call.'
        )
        self._queue.append((func, args, kwargs))
        return None

      result = func(*args, **kwargs)

      dispatcher.send(
        signal=self._custom_signal, sender=self._custom_sender, data=result
      )
      return result

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
      if hasattr(method, '_signal') and hasattr(method, '_original_func'):
        bound_method = method.__get__(instance, instance.__class__)
        dispatcher.connect(
          receiver=bound_method, signal=method._signal, sender=method._sender
        )
        logging.info(
          f'Connected {name} to signal: {method._signal} with sender: {method._sender}'
        )
