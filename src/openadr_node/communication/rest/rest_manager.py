from datetime import timezone, datetime
import numpy as np
from flask import jsonify, Response
from typing import Any, Dict, Optional, Callable, Tuple, List
from werkzeug.serving import make_server

from src.openadr_node import logger
from src.openadr_node.database.interfaces.services.iconsumption_service import (
  IConsumptionService,
)
from src.openadr_node.database.interfaces.services.iloadprofile_service import (
  ILoadProfileService,
)
from src.openadr_node.decorator.rest_endpoint import rest_endpoint
from src.openadr_node.database.interfaces.database_interface import IRestAPIController


class RestAPIController(IRestAPIController):
  """
  Manages the REST API for the OpenADR node.

  This class initializes a Flask server to handle REST API requests.
  It provides endpoints for retrieving load profiler and consumption data.
  The actual server running is handled by the NodeController.

  Attributes:
      app (Flask): The Flask application instance.
      _rest_api_port (int): The port on which the REST API runs.
      _energy_db_controller (Any): The load profiler manager instance.
      _get_current_consumption_callback (Any): Callback for getting current consumption.
      _server (werkzeug.serving.BaseWSGIServer): The WSGI server instance.
  """

  def __init__(
    self,
    port: int,
    load_profile_service: ILoadProfileService,
    consumption_service: IConsumptionService,
  ) -> None:
    """
    Initialize the REST API manager.

    Args:
        port (int): Port for the REST API.
    """
    # self.app = Flask(__name__)
    self._rest_api_port = port
    self._load_profile_service = load_profile_service
    self._consumption_service = consumption_service
    self._get_current_consumption_callback: Optional[Callable[[], Dict[str, Any]]] = (
      None
    )
    self._server = None

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

  def serve_forever(self) -> None:
    """
    Start the Flask server. This method is called by the NodeController's thread manager.
    """
    self.init_routes(self)
    if self._server is None:
      self._server = make_server('0.0.0.0', self._rest_api_port, self.app)
    try:
      self._server.serve_forever()
    except Exception as e:
      logger.error(f'Failed to start Flask server: {e}')
      raise

  def shutdown(self) -> None:
    """
    Shutdown the Flask server cleanly.
    """
    if self._server:
      logger.info('Shutting down Flask server...')
      self._server.shutdown()
      self._server = None
      logger.info('Flask server shut down successfully.')

  def _check_manager_initialized(self) -> Optional[Tuple[Response, int]]:
    """
    Check if the load profiler manager is initialized.

    Returns:
        Optional[Tuple[Response, int]]: JSON response if not initialized, otherwise None.
    """
    if self._consumption_service or self._load_profile_service is None:
      return jsonify({'error': 'Database services not initialized'}), 500
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
        Optional[Tuple[Response, int]]: JSON response if data not found, otherwise None.
    """
    if not data or not any(arr.size for arr in data.values()):
      return jsonify({'error': f'{data_type} not found'}), 404
    return None

  @rest_endpoint('/data/load_profile')
  def get_load_profile(self) -> Any:
    """Get the load profiler data."""
    try:
      response = self._check_manager_initialized()
      if response:
        return response

      df = self._load_profile_service.get_load_profile_data()
      response = self._check_data_exists(df, 'Load profiler')
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
      logger.error(f'Failed to serialize load profiler: {e}')
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
    """Get the current consumption data with Unix timestamp in milliseconds."""
    try:
      response = self._check_manager_initialized()
      if response:
        return response

      current_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

      consumption_points = self._consumption_service.get_closest_consumption_points(
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
