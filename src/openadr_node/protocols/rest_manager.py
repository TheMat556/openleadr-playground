from datetime import timezone, datetime

import numpy as np
from flask import Flask, jsonify
from typing import Any, Dict
import logging

from src.openadr_node.decorator.rest_endpoint import rest_endpoint

logger = logging.getLogger(__name__)


class RestApiManager:
  def __init__(self, port: int):
    """
    Initialize the REST API manager.

    :param port: Port for the REST API.
    :type port: int
    """
    self.app = Flask(__name__)
    self._rest_api_port = port
    self._load_profile_manager = None
    self._get_current_consumption_callback = None

  def set_load_profile_manager(self, load_profile_manager: Any) -> None:
    """
    Set the load profile manager instance.

    :param load_profile_manager: The load profile manager instance
    :type load_profile_manager: Any
    """
    self._load_profile_manager = load_profile_manager

  def init_routes(self, instance: Any) -> None:
    """
    Initialize the REST API routes.

    :param instance: Instance containing the route methods
    :type instance: Any
    """
    for attr_name in dir(instance):
      attr = getattr(instance, attr_name)
      if callable(attr) and getattr(attr, '_rest_endpoint', False):
        self.app.add_url_rule(attr._rest_path, view_func=attr, methods=['GET'])

  def run(self) -> None:
    """
    Run the Flask server.
    """
    try:
      self.app.run(host='0.0.0.0', port=self._rest_api_port)
    except OSError as e:
      logger.error(f'Failed to start Flask server: {e}')
      raise

  def _check_manager_initialized(self) -> Any:
    """
    Check if the load profile manager is initialized.

    :return: JSON response if not initialized, otherwise None.
    :rtype: Any
    """
    if self._load_profile_manager is None:
      return jsonify({'error': 'Load profile manager not initialized'}), 500
    return None

  def _check_data_exists(self, data: Dict[str, np.ndarray], data_type: str) -> Any:
    """
    Check if the data exists.

    :param data: Dictionary of numpy arrays to check.
    :type data: Dict[str, np.ndarray]
    :param data_type: Type of data being checked.
    :type data_type: str
    :return: JSON response if data not found, otherwise None.
    :rtype: Any
    """
    if data is None or not any(arr.size for arr in data.values()):
      return jsonify({'error': f'{data_type} not found'}), 404
    return None

  @rest_endpoint('/data/load_profile')
  def get_load_profile(self) -> Any:
    try:
      response = self._check_manager_initialized()
      if response:
        return response

      df = self._load_profile_manager.get_load_profile()
      response = self._check_data_exists(df, 'Load profile')
      if response:
        return response

      print('DATA123', df)
      formatted_data = {
        str(int(df['dstart'][i])): {
          'duration': int(df['duration'][i]),
          'signal_payload': float(df['signal_payload'][i]),
        }
        for i in range(len(df['dstart']))
      }

      return jsonify(formatted_data), 200, {'Content-Type': 'application/json'}
    except Exception as e:
      logger.error(f'Failed to serialize load profile: {e}')
      return jsonify({'error': 'Failed to serialize data'}), 500

  @rest_endpoint('/data/consumption')
  def get_current_consumption(self) -> Any:
    """
    Get the current consumption data with Unix timestamp in milliseconds.

    Returns:
        tuple: A tuple containing (Response, status_code) or (Response, status_code, headers)
               Response contains consumption data in JSON format or error message
    """
    try:
      response = self._check_manager_initialized()
      if response:
        return response

      current_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

      consumption_points = self._load_profile_manager.get_closest_consumption_points(
        current_timestamp
      )
      if not consumption_points:  # Check if the list is empty
        return jsonify({'error': 'Consumption data not found'}), 404

      logger.debug(f'Retrieved consumption points: {consumption_points}')

      # If consumption_points is a list of dictionaries, calculate sum of 'value' key
      try:
        overall_value = sum(point['value'] for point in consumption_points)
        ven_id = consumption_points[0]['ven_id']  # Get ven_id from first point
      except (KeyError, TypeError) as e:
        logger.error(f'Invalid data structure in consumption points: {e}')
        return jsonify({'error': 'Invalid data structure'}), 500

      logger.debug(f'Calculated overall value: {overall_value}')

      consumption_data = {
        'ven_id': ven_id,
        'overall_value': overall_value,
        'unit': 'kWh',
        'timestamp': current_timestamp,
      }

      return jsonify(consumption_data), 200, {'Content-Type': 'application/json'}
    except Exception as e:
      logger.error(f'Failed to retrieve consumption data: {e}')
      return jsonify({'error': 'Failed to retrieve data'}), 500
