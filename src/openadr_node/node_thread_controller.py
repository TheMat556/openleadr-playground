from threading import Thread
from typing import Callable, List


class NodeThreadController:
  """
  Controller for managing threads in the node.

  Attributes
  ----------
  threads : List[Thread]
      List to store active threads.
  """

  def __init__(self):
    """
    Initialize the NodeThreadController.
    """
    self._threads: List[Thread] = []

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
    thread = Thread(target=target, name=name, daemon=True)
    thread.start()
    self._threads.append(thread)

  def join_threads(self, timeout: float = 5.0) -> None:
    """
    Join all threads with an optional timeout.

    Parameters
    ----------
    timeout : float, optional
        The timeout for joining threads, by default 5.0.
    """
    for thread in self._threads:
      thread.join(timeout)
    self._threads.clear()
