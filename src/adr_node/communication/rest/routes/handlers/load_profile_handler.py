from flask import Response
import numpy as np

from src.adr_node.communication.rest.routes.decorators.route_decorator import api_route
from src.adr_node.database.interfaces.services.iloadprofile_service import (
  ILoadProfileService,
)
from src.openadr_node import logger


class NumpyJSONEncoder:
  """
  Encoder for numpy data types to ensure JSON serialization compatibility.
  """

  @staticmethod
  def encode_numpy(obj):
    if isinstance(obj, np.ndarray):
      return obj.tolist()
    if isinstance(obj, np.integer):
      return int(obj)
    if isinstance(obj, np.floating):
      return float(obj)
    return obj


def sanitize_for_json(data):
  """
  Recursively sanitize data for JSON serialization.

  Args:
      data: The data to sanitize.

  Returns:
      The sanitized data.
  """
  if isinstance(data, dict):
    return {k: sanitize_for_json(v) for k, v in data.items()}
  if isinstance(data, list):
    return [sanitize_for_json(item) for item in data]
  if isinstance(data, (np.ndarray, np.integer, np.floating)):
    return NumpyJSONEncoder.encode_numpy(data)
  if isinstance(data, Response):
    return None
  return data


class LoadProfileHandler:
  """
  Handler for load profile-related API endpoints.

  This class provides methods to handle requests for load profile data.
  """

  def __init__(self, load_profile_service: ILoadProfileService):
    self.load_profile_service = load_profile_service

  @api_route('/api/load-profile', methods=['GET'])
  def get_load_profile(self):
    """
    Get the load profile data.

    Returns:
        JSON response containing the load profile data.
    """
    try:
      data = self.load_profile_service.get_load_profile_data()

      processed_data = sanitize_for_json(data)

      return processed_data

    except Exception as e:
      logger.error(f'Error processing load profile data: {str(e)}')
      raise
