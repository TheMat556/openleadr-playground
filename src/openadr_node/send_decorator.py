from functools import wraps
from pydispatch import dispatcher
import logging

logger = logging.getLogger(__name__)

class SendDispatcher:
    def __init__(self, signal=None, sender=None):
        """
        Initialize the SendDispatcher decorator.

        Args:
            signal (str, optional): Custom signal to use. If not provided, the method name will be used.
            sender (str, optional): Custom sender to use. Defaults to `None`.
        """
        self._custom_signal = signal
        self._custom_sender = sender
        self._ready_dispatched = False  # Flag to track if "on_ready" event has been dispatched

        # Register listener for the "on_ready" event
        dispatcher.connect(self.on_ready, signal="on_ready", sender=dispatcher.Any)

    def on_ready(self, sender):
        """
        This method is called when the "on_ready" event is dispatched.
        It will enable the dispatching of the `register_dispatcher` event.
        """
        logger.info("on_ready event received. Ready to register dispatchers.")
        if not self._ready_dispatched:
            # Dispatch the "register_dispatcher" event only once when "on_ready" is received
            dispatcher.send(signal="register_dispatcher", sender=self._custom_sender, data=self._custom_signal)
            logger.info(f"Dispatched 'register_dispatcher' signal from {self._custom_sender}")
            self._ready_dispatched = True

    def decorate(self, func):
        """
        Decorate a method to connect it to a signal at runtime.

        Args:
            func (callable): The function to connect to the signal.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self._ready_dispatched:
                logger.warning("on_ready event has not been dispatched. Aborting function call.")
                return None  # Optionally handle this with a return value or exception

            # Call the original function and capture the result
            result = func(*args, **kwargs)

            # Send the event with the result
            dispatcher.send(signal=self._custom_signal, sender=self._custom_sender, data=result)
            logger.info(f"Dispatched signal '{self._custom_signal}' with result: {result}")

            return result

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
            if hasattr(method, "_signal") and hasattr(method, "_original_func"):
                # Create a bound method for the instance
                bound_method = method.__get__(instance, instance.__class__)

                # Connect the bound method to the dispatcher
                dispatcher.connect(
                    receiver=bound_method,
                    signal=method._signal,
                    sender=method._sender
                )
                logger.info(
                    f"Connected {name} to signal: {method._signal} with sender: {method._sender}"
                )
