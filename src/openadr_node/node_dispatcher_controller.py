from pydispatch import dispatcher
from typing import Optional, Callable, Any
from src.openadr_node import logger


class NodeDispatcherController:
  """
  Manages PyDispatch signal handling and routing for the OpenADR node system.
  Works in conjunction with NodeManager to handle signal dispatching.

  Attributes
  ----------
  node_manager : NodeManager
      Instance of NodeManager that contains signal handling methods.
  """

  def __init__(self, node_manager):
    """
    Initialize the DispatcherManager with a reference to the NodeManager instance.

    Parameters
    ----------
    node_manager : NodeManager
        Instance of NodeManager that contains signal handling methods.
    """
    self._node_manager = node_manager

  def get_method(self, signal: str) -> Optional[Callable]:
    """
    Get the method associated with a signal from the node manager.

    Parameters
    ----------
    signal : str
        The signal name.

    Returns
    -------
    Optional[Callable]
        The method associated with the signal.
    """
    method_name = f'_on_{signal}'
    return getattr(self._node_manager, method_name, None)

  def register_dispatcher(self, sender: str, signal: str, data: str) -> None:
    """
    Register a dispatcher for a signal.

    Parameters
    ----------
    sender : str
        The sender of the signal.
    signal : str
        The signal name.
    data : str
        The data associated with the signal.
    """
    method = self.get_method(data)
    if callable(method):
      dispatcher.connect(self._call_method, signal=data, sender=dispatcher.Any)
    else:
      dispatcher.connect(self._forward_dispatcher, signal=data, sender=sender)

    logger.info(
      f'DispatcherManager - Connected _on{signal} to signal: {data} with sender: {sender}'
    )

  def _forward_dispatcher(self, sender: str, signal: str, data: Any) -> None:
    """
    Forward a dispatcher signal using the node manager's methods.

    Parameters
    ----------
    sender : str
        The sender of the signal.
    signal : str
        The signal name.
    data : Any
        The data associated with the signal.
    """
    dispatcher.send(signal=signal, sender='nm', data=data)

  def _call_method(self, sender: str, signal: str, data: Any) -> None:
    """
    Call the appropriate method on the node manager associated with a signal.

    Parameters
    ----------
    sender : str
        The sender of the signal.
    signal : str
        The signal name.
    data : Any
        The data associated with the signal.
    """
    if sender == 'nm':
      return

    method = self.get_method(signal)
    if callable(method):
      try:
        method(sender, data)
      except Exception as e:
        logger.error(f'Error calling method {signal}: {e}')
        raise
