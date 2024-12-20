from typing import Callable


def rest_endpoint(path: str) -> Callable:
  """
  Decorator to mark a method as a REST endpoint.

  :param path: The URL path for the endpoint.
  :type path: str
  :return: The decorated function.
  :rtype: Callable
  """

  def decorator(func: Callable) -> Callable:
    func._rest_endpoint = True
    func._rest_path = path
    return func

  return decorator
