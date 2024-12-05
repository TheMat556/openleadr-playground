from functools import wraps
from pydispatch import dispatcher
import logging

logger = logging.getLogger(__name__)

class SendDispatcher:
    def __init__(self, signal=None, sender=None):
        """
        Initialize the SendDispatcher decorator.

        Args:
            signal (str, optional): Signal to dispatch. If not provided, the method name will be used.
            sender (str, optional): Sender to use for the dispatch. Defaults to `None`.
        """
        self._custom_signal = signal
        self._custom_sender = sender

    def decorate(self, func):
        print("!!!!1dqdasd")
        """
        Decorate a method to send a signal before execution and after execution.

        Args:
            func (callable): The function to wrap.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Instance of the class (first argument)
            instance = args[0]  # Assuming the first argument is `self` (instance method)
            signal = self._custom_signal or func.__name__
            sender = self._custom_sender
            # 1. Pre-send signal (before the method execution)
            logger.info(f"Pre-sending signal: {signal} from sender: {sender}")
            if not instance._ready:
                logger.debug(f"Queuing pre-signal: {signal} from sender: {sender}")
                instance._deferred_signals.append((signal, sender, kwargs))
            else:
                logger.debug(f"Dispatching pre-signal: {signal} from sender: {sender}")
                dispatcher.send(signal=signal, sender=sender, **kwargs)

            # 2. Call the original method (this will execute after pre-signal is dispatched)
            result = func(*args, **kwargs)

            # 3. Post-send signal (after the method execution)
            if not instance._ready:
                logger.debug(f"Queuing post-signal: {signal} from sender: {sender}")
                instance._deferred_signals.append((signal, sender, kwargs))
            else:
                logger.debug(f"Dispatching post-signal: {signal} from sender: {sender}")
                dispatcher.send(signal=signal, sender=sender, **kwargs)

            return result

        return wrapper

    def __call__(self, func):
        """
        Callable method for the decorator, delegates to `decorate`.
        """
        return self.decorate(func)


