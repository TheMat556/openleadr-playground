from functools import wraps
from pydispatch import dispatcher
import logging
import time
from typing import Callable, Any, Tuple, Optional
from collections import deque
from threading import Lock

MAX_QUEUE_SIZE = 1000
MAX_METRICS_HISTORY = 1000


class SignalSender:
  """
  A decorator class for sending signals using the pydispatch library.
  """

  def __init__(
    self,
    signal: Optional[str] = None,
    sender: Optional[str] = None,
    max_retries: int = 3,
  ) -> None:
    """
    Initialize the SendDispatcher decorator.

    :param signal: Custom signal to use. If not provided, the method name will be used.
    :type signal: str, optional
    :param sender: Custom sender to use. Defaults to `None`.
    :type sender: str, optional
    :param max_retries: Maximum number of retries for failed dispatches.
    :type max_retries: int
    """
    self._custom_signal = signal
    self._custom_sender = sender
    self._ready_dispatched = False
    self._queue: deque[Tuple[Callable, Tuple[Any], dict]] = deque(maxlen=MAX_QUEUE_SIZE)
    self._queue_lock = Lock()
    self._max_retries = max_retries
    self._metrics = {
      'queue_size': 0,
      'processing_times': deque(maxlen=MAX_METRICS_HISTORY),
    }

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

      with self._queue_lock:
        while self._queue:
          func, args, kwargs = self._queue.popleft()
          self._process(func, args, kwargs)

  def _process(self, func: Callable, args: Tuple[Any], kwargs: dict) -> None:
    retries = 0
    while retries < self._max_retries:
      try:
        start_time = time.time()
        result = func(*args, **kwargs)
        dispatcher.send(
          signal=self._custom_signal, sender=self._custom_sender, data=result
        )
        end_time = time.time()
        with self._queue_lock:
          self._metrics['processing_times'].append(end_time - start_time)
        break
      except Exception as e:
        logging.error(f'Error processing signal {self._custom_signal}: {e}')
        retries += 1
        if retries >= self._max_retries:
          logging.error(f'Max retries reached for signal {self._custom_signal}')

  def decorate(self, func: Callable) -> Callable:
    """
    Decorate a method to connect it to a signal at runtime.

    :param func: The function to connect to the signal.
    :type func: Callable
    :return: The wrapped function.
    :rtype: Callable
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Optional[Any]:
      """
      Wrapper function that handles signal dispatch and queuing.

      Args:
          *args: Variable positional arguments for the wrapped function
          **kwargs: Variable keyword arguments for the wrapped function

      Returns:
          Optional[Any]: The result of the function if processed immediately,
                       None if queued for later processing
      """
      if not self._ready_dispatched:
        logging.warning(
          'on_ready event has not been dispatched. Queuing function call.'
        )
        with self._queue_lock:
          if len(self._queue) >= MAX_QUEUE_SIZE:
            raise RuntimeError('Signal queue is full')
          self._queue.append((func, args, kwargs))
          self._metrics['queue_size'] = len(self._queue)
        return None

      self._process(func, args, kwargs)

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
