from typing import Callable


def rest_endpoint(path: str) -> Callable:
  """
  Decorator to mark a method as a REST endpoint.

  :param path: The URL path for the endpoint.
  :type path: str
  :return: The decorated function.
  :rtype: Callable
  """
  if not path.startswith('/'):
    raise ValueError("Path must start with '/'")
  if not all(c.isalnum() or c in {'/', '_'} for c in path):
    raise ValueError('Path contains invalid characters')

  def decorator(func: Callable) -> Callable:
    func._rest_endpoint = True
    func._rest_path = path
    return func

  return decorator
