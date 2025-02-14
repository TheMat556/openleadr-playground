# routes/decorators/route_decorator.py
from functools import wraps
from typing import Callable, Type, Optional
from flask import jsonify
from datetime import datetime

from src.adr_node.communication.rest.domain.api_response import ApiResponse


def api_route(
  endpoint: str, methods: list[str] = ['GET'], response_model: Optional[Type] = None
):
  """
  Decorator to define an API route.

  Parameters
  ----------
  endpoint : str
      The endpoint for the API route.
  methods : list[str], optional
      The HTTP methods allowed for the route, default is ['GET'].
  response_model : Optional[Type], optional
      The model to use for the response, default is None.

  Returns
  -------
  Callable
      The decorated function.
  """

  def decorator(f: Callable):
    @wraps(f)
    def wrapped(*args, **kwargs):
      try:
        result = f(*args, **kwargs)
        if response_model and not isinstance(result, response_model):
          result = response_model(**result)

        response = ApiResponse(
          status='success',
          timestamp=datetime.utcnow(),
          data=result.__dict__ if hasattr(result, '__dict__') else result,
        )
        return jsonify(response.__dict__)
      except Exception as e:
        response = ApiResponse(
          status='error', timestamp=datetime.utcnow(), error=str(e)
        )
        return jsonify(response.__dict__), 500

    # Store route info for registration
    wrapped._endpoint = endpoint
    wrapped._methods = methods
    return wrapped

  return decorator
