from threading import Thread
from typing import Callable


class ThreadManager:
  def __init__(self):
    self._threads = []

  def start_thread(self, target: Callable, name: str) -> None:
    """
    Start a new thread with the given target function and name.

    :param target: The target function to run in the thread.
    :type target: Callable
    :param name: The name of the thread.
    :type name: str
    """
    thread = Thread(target=target, name=name, daemon=True)
    thread.start()
    self._threads.append(thread)

  def join_threads(self, timeout: float = 5.0) -> None:
    """
    Join all threads with an optional timeout.

    :param timeout: The timeout for joining threads.
    :type timeout: float
    """
    for thread in self._threads:
      thread.join(timeout)
    self._threads.clear()
