from flask import Flask, jsonify
from typing import Any, Optional, Dict
import logging
from werkzeug.serving import make_server
import threading
import signal

from src.openadr_node.decorator.rest_endpoint import rest_endpoint

logger = logging.getLogger(__name__)


class RestApiManager:
  def __init__(self, port: int):
    """
    Initialize the REST API manager.

    Args:
        port (int): Port for the REST API.
    """
    self.app = Flask(__name__)
    self._rest_api_port = port
    self._load_profile_manager = None
    self._get_current_consumption_callback = None
    self._server = None
    self._shutdown_event = threading.Event()

    # Configure Flask for production
    self.app.config['ENV'] = 'production'
    self.app.config['DEBUG'] = False

    # Add basic security headers
    @self.app.after_request
    def add_security_headers(response):
      response.headers['X-Content-Type-Options'] = 'nosniff'
      response.headers['X-Frame-Options'] = 'SAMEORIGIN'
      response.headers['X-XSS-Protection'] = '1; mode=block'
      return response

  def set_load_profile_manager(self, load_profile_manager: Any) -> None:
    """
    Set the load profile manager instance.

    Args:
        load_profile_manager: The load profile manager instance
    """
    self._load_profile_manager = load_profile_manager

  def init_routes(self, instance: Any) -> None:
    """
    Initialize the REST API routes.

    Args:
        instance: Instance containing the route methods
    """
    for attr_name in dir(instance):
      attr = getattr(instance, attr_name)
      if callable(attr) and getattr(attr, '_rest_endpoint', False):
        self.app.add_url_rule(attr._rest_path, view_func=attr, methods=['GET'])

  def _setup_signal_handlers(self) -> None:
    """Set up signal handlers for graceful shutdown."""

    def signal_handler(signum, frame):
      logger.info(f'Received signal {signum}. Initiating graceful shutdown...')
      self.stop()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

  def start(self) -> None:
    """
    Start the Flask server in a separate thread with proper configuration.
    """
    self._setup_signal_handlers()

    def run_flask_server() -> None:
      try:
        logger.info(f'Starting Flask server on port {self._rest_api_port}')
        # Use Werkzeug's production server
        self._server = make_server(
          host='0.0.0.0',
          port=self._rest_api_port,
          app=self.app,
          threaded=True,
          processes=1,  # Single process for better control
        )
        self._server.serve_forever()
      except OSError as e:
        logger.error(f'Failed to start Flask server: {e}')
        raise

    self._server_thread = threading.Thread(target=run_flask_server)
    self._server_thread.daemon = True
    self._server_thread.start()

  def stop(self) -> None:
    """
    Gracefully stop the server.
    """
    if self._server:
      logger.info('Shutting down Flask server...')
      self._server.shutdown()
      self._shutdown_event.set()

  def _safe_df_access(self, df) -> Optional[Dict]:
    """
    Safely access DataFrame and handle empty cases.

    Args:
        df: pandas DataFrame to check

    Returns:
        Optional[Dict]: Error response if DataFrame is invalid, None if valid
    """
    if df is None or df.empty:
      return {'error': 'No data found'}, 404
    return None

  @rest_endpoint('/data/load_profile')
  def get_load_profile(self) -> Any:
    """
    Get the load profile data.

    Returns:
        Any: The load profile data in JSON format.
    """
    try:
      if self._load_profile_manager is None:
        return jsonify({'error': 'Load profile manager not initialized'}), 500

      df = self._load_profile_manager.get_load_profile()
      error = self._safe_df_access(df)
      if error:
        return jsonify(error[0]), error[1]

      load_profile_dict = df.to_dict(orient='index')
      formatted_data = {
        str(timestamp): {
          'duration': values['duration'],
          'signal_payload': values['signal_payload'],
        }
        for timestamp, values in load_profile_dict.items()
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
        Any: The current consumption data in JSON format.
    """
    try:
      if self._load_profile_manager is None:
        return jsonify({'error': 'Load profile manager not initialized'}), 500

      df = self._load_profile_manager.get_consumption()
      error = self._safe_df_access(df)
      if error:
        return jsonify(error[0]), error[1]

      try:
        latest_consumption = df.iloc[-1]
      except IndexError:
        return jsonify({'error': 'No consumption data available'}), 404

      consumption_data = {
        'consumption': {
          'value': latest_consumption['value'],
          'timestamp': str(latest_consumption.name),
          'unit': 'kWh',
        }
      }
      return jsonify(consumption_data), 200, {'Content-Type': 'application/json'}
    except Exception as e:
      logger.error(f'Failed to retrieve consumption data: {e}')
      return jsonify({'error': 'Failed to retrieve data'}), 500
