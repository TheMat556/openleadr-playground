from pydispatch import dispatcher
from typing import Optional, Callable, Any, TYPE_CHECKING
from src.openadr_node import logger

if TYPE_CHECKING:
  from src.openadr_node import NodeController


class NodeDispatcherController:
  """
  Manages PyDispatch signal handling and routing for the OpenADR node system.
  Works in conjunction with NodeController to handle signal dispatching.

  Attributes
  ----------
  node_controller : NodeController
      Instance of NodeManager that contains signal handling methods.
  """

  def __init__(self, node_controller: 'NodeController'):
    """
    Initialize the DispatcherManager with a reference to the NodeManager instance.

    Parameters
    ----------
    node_controller : NodeManager
        Instance of NodeManager that contains signal handling methods.
    """
    self._node_manager = node_controller

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

  def register_dispatcher(
    self, sender: str, signal: str, dispatcher_signal: str
  ) -> None:
    """
    Register a dispatcher for a signal.

    Parameters
    ----------
    sender : str
        The sender of the signal.
    signal : str
        The signal name.
    dispatcher_signal : str
        The dispatcher signal name.
    """
    method = self.get_method(dispatcher_signal)
    if callable(method):
      dispatcher.connect(
        self._call_method, signal=dispatcher_signal, sender=dispatcher.Any
      )
    else:
      dispatcher.connect(
        self._forward_dispatcher, signal=dispatcher_signal, sender=sender
      )

    logger.info(
      f'DispatcherManager - Connected _on{signal} to signal: {dispatcher_signal} with sender: {sender}'
    )

  @staticmethod
  def _forward_dispatcher(sender: str, signal: str, data: Any) -> None:
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
        logger.error(
          f'Error calling method {signal} from sender {sender} with data {data}: {e}'
        )
        raise
