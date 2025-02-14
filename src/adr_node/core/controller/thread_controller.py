from threading import Thread, Lock
from typing import Callable, List

from src.openadr_node import logger


class ThreadController:
  """
  Controller for managing threads in the node.

  Attributes
  ----------
  _threads : List[Thread]
      List to store active threads.
  _lock : Lock
      Lock to ensure thread safety.
  """

  def __init__(self):
    """
    Initialize the ThreadController.
    """
    self._threads: List[Thread] = []
    self._lock = Lock()

  def start_thread(self, target: Callable, name: str) -> None:
    """
    Start a new thread with the given target function and name.

    Parameters
    ----------
    target : Callable
        The target function to run in the thread.
    name : str
        The name of the thread.
    """
    try:
      thread = Thread(target=target, name=name, daemon=True)
      thread.start()
      with self._lock:
        self._threads.append(thread)
      logger.info(f'Thread {name} started successfully.')
    except Exception as e:
      logger.error(f'Failed to start thread {name}: {e}')

  def join_threads(self, timeout: float = 5.0) -> None:
    """
    Join all threads with an optional timeout.

    Parameters
    ----------
    timeout : float, optional
        The timeout for joining threads, by default 5.0.
    """
    with self._lock:
      for thread in self._threads:
        try:
          thread.join(timeout)
          if thread.is_alive():
            logger.warning(f'Thread {thread.name} did not finish within the timeout.')
        except Exception as e:
          logger.error(f'Error joining thread {thread.name}: {e}')
      self._threads.clear()
