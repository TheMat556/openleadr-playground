import asyncio
from typing import Callable, Dict, List, Optional
import threading

class AsyncEventDispatcher:
  _instance = None
  _lock = threading.Lock()

  def __new__(cls):
    """
    Singleton implementation to ensure only one instance exists.
    """
    if not cls._instance:
      with cls._lock:
        if not cls._instance:
          cls._instance = super().__new__(cls)
          cls._instance._subscribers = {}
    return cls._instance

  def __init__(self):
    """
    Initialize the event dispatcher if not already initialized.
    """
    if not hasattr(self, '_subscribers'):
      self._subscribers: Dict[str, List[Callable]] = {}

  def subscribe(self, event_type: str, callback: Callable):
    """
    Subscribe a callback to a specific event type.

    :param event_type: The type of event to subscribe to
    :param callback: Function to be called when the event occurs
    """
    if event_type not in self._subscribers:
      self._subscribers[event_type] = []

    if callback not in self._subscribers[event_type]:
      self._subscribers[event_type].append(callback)

  async def publish(self, event_type: str, **kwargs):
    """
    Publish an event to all subscribers.

    :param event_type: The type of event to publish
    :param kwargs: Optional keyword arguments to pass to subscribers
    """
    if event_type not in self._subscribers:
      return

    for subscriber in self._subscribers[event_type]:
      # Handle both async and sync callbacks
      if asyncio.iscoroutinefunction(subscriber):
        await subscriber(**kwargs)
      else:
        subscriber(**kwargs)

  def unsubscribe(self, event_type: str, callback: Optional[Callable] = None):
    """
    Unsubscribe from an event type.

    :param event_type: The event type to unsubscribe from
    :param callback: Optional specific callback to remove
    """
    if event_type not in self._subscribers:
      return

    if callback is None:
      # Remove all subscribers for this event type
      self._subscribers[event_type].clear()
    elif callback in self._subscribers[event_type]:
      self._subscribers[event_type].remove(callback)

# Create a global dispatcher instance
dispatcher = AsyncEventDispatcher()
