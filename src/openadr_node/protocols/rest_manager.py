from datetime import timezone, datetime
import numpy as np
from flask import Flask, jsonify, request, Response
from typing import Any, Dict, Optional, Callable, Tuple, List
import threading

from src.openadr_node import logger
from src.openadr_node.database.energy_database_controller import (
  EnergyDatabaseController,
)
from src.openadr_node.decorator.rest_endpoint import rest_endpoint


class RestAPIController:
  """
  Manages the REST API for the OpenADR node.

  This class initializes and runs a Flask server to handle REST API requests.
  It provides endpoints for retrieving load profile and consumption data.

  Attributes:
      app (Flask): The Flask application instance.
      _rest_api_port (int): The port on which the REST API runs.
      _load_profile_manager (Any): The load profile manager instance.
      _get_current_consumption_callback (Any): Callback for getting current consumption.
      server_thread (threading.Thread): The thread running the Flask server.
  """

  def __init__(self, port: int):
    """
    Initialize the REST API manager.

    Args:
        port (int): Port for the REST API.
    """
    self.app = Flask(__name__)
    self._rest_api_port = port
    self._load_profile_manager: Optional[EnergyDatabaseController] = None
    self._get_current_consumption_callback: Optional[Callable[[], Dict[str, Any]]] = (
      None
    )
    self.server_thread = None

  def set_load_profile_manager(self, load_profile_manager: Any) -> None:
    """
    Set the load profile manager instance.

    Args:
        load_profile_manager (Any): The load profile manager instance.
    """
    self._load_profile_manager = load_profile_manager

  def init_routes(self, instance: Any) -> None:
    """
    Initialize the REST API routes.

    Args:
        instance (Any): Instance containing the route methods.
    """
    for attr_name in dir(instance):
      attr = getattr(instance, attr_name)
      if callable(attr) and getattr(attr, '_rest_endpoint', False):
        self.app.add_url_rule(attr._rest_path, view_func=attr, methods=['GET'])

  def run(self) -> None:
    """
    Run the Flask server in a separate thread.
    """

    def run_server():
      try:
        self.app.run(host='0.0.0.0', port=self._rest_api_port)
      except OSError as e:
        logger.error(f'Failed to start Flask server: {e}')
        raise

    self.server_thread = threading.Thread(target=run_server)
    self.server_thread.start()

  def shutdown_server(self) -> None:
    """
    Shutdown the Flask server.
    """
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
      raise RuntimeError('Not running the Werkzeug Server')
    func()

  def __del__(self):
    """
    Ensure the Flask server is shut down when the instance is destroyed.
    """
    if self.server_thread and self.server_thread.is_alive():
      logger.info('Shutting down Flask server...')
      self.shutdown_server()
      self.server_thread.join()
      logger.info('Flask server shut down successfully.')

  def _check_manager_initialized(self) -> Optional[Tuple[Response, int]]:
    """
    Check if the load profile manager is initialized.

    Returns:
        Any: JSON response if not initialized, otherwise None.
    """
    if self._load_profile_manager is None:
      return jsonify({'error': 'Load profile manager not initialized'}), 500
    return None

  def _check_data_exists(
    self, data: Dict[str, np.ndarray], data_type: str
  ) -> Optional[Tuple[Response, int]]:
    """
    Check if the data exists.

    Args:
        data (Dict[str, np.ndarray]): Dictionary of numpy arrays to check.
        data_type (str): Type of data being checked.

    Returns:
        Any: JSON response if data not found, otherwise None.
    """
    if not data or not any(arr.size for arr in data.values()):
      return jsonify({'error': f'{data_type} not found'}), 404
    return None

  @rest_endpoint('/data/load_profile')
  def get_load_profile(self) -> Any:
    """
    Get the load profile data.

    Returns:
        Any: JSON response containing the load profile data or an error message.
    """
    try:
      response = self._check_manager_initialized()
      if response:
        return response

      df = self._load_profile_manager.get_load_profile()
      response = self._check_data_exists(df, 'Load profile')
      if response:
        return response

      formatted_data = {
        str(int(start)): {'duration': int(dur), 'signal_payload': float(payload)}
        for start, dur, payload in zip(
          df['dstart'], df['duration'], df['signal_payload']
        )
      }

      return jsonify(formatted_data), 200, {'Content-Type': 'application/json'}
    except Exception as e:
      logger.error(f'Failed to serialize load profile: {e}')
      return jsonify({'error': 'Failed to serialize data'}), 500

  def _process_consumption_points(
    self, points: List[Dict[str, Any]]
  ) -> Tuple[float, str]:
    """Process consumption points to extract overall value and ven_id."""
    if not points:
      raise ValueError('Empty consumption points')
    overall_value = sum(point['value'] for point in points)
    ven_id = points[0]['ven_id']
    return overall_value, ven_id

  @rest_endpoint('/data/consumption')
  def get_current_consumption(self) -> Any:
    """
    Get the current consumption data with Unix timestamp in milliseconds.

    Returns:
        Any: JSON response containing the consumption data or an error message.
    """
    try:
      response = self._check_manager_initialized()
      if response:
        return response

      current_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

      consumption_points = self._load_profile_manager.get_closest_consumption_points(
        current_timestamp
      )
      if not consumption_points:
        return jsonify({'error': 'Consumption data not found'}), 404

      logger.debug(f'Retrieved consumption points: {consumption_points}')

      try:
        overall_value, ven_id = self._process_consumption_points(consumption_points)
      except ValueError as e:
        logger.error(f'Failed to process consumption points: {e}')
        return jsonify({'error': str(e)}), 500

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
