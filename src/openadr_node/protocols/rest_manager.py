from flask import Flask, jsonify
from threading import Thread
from typing import Any
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

  def start(self) -> None:
    """
    Start the Flask server in a separate thread.
    """

    def run_flask() -> None:
      try:
        self.app.run(host='0.0.0.0', port=self._rest_api_port)
      except OSError as e:
        logger.error(f'Failed to start Flask server: {e}')
        raise

    thread = Thread(target=run_flask)
    thread.daemon = True
    thread.start()

  @rest_endpoint('/data/load_profile')
  def get_load_profile(self) -> Any:
    """
    Get the load profile data.

    :return: The load profile data in JSON format.
    :rtype: Any
    """
    try:
      if self._load_profile_manager is None:
        return jsonify({'error': 'Load profile manager not initialized'}), 500

      df = self._load_profile_manager.get_load_profile()
      if df is None or df.empty:
        return jsonify({'error': 'Load profile not found'}), 404

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

    :return: The current consumption data in JSON format.
    :rtype: Any
    """
    try:
      if self._load_profile_manager is None:
        return jsonify({'error': 'Load profile manager not initialized'}), 500

      df = self._load_profile_manager.get_consumption()
      if df is None or df.empty:
        return jsonify({'error': 'No consumption data found'}), 404

      latest_consumption = df.iloc[-1]
      consumption_data = {
        'consumption': {
          'value': latest_consumption['value'],
          'timestamp': str(latest_consumption.name),  # The index is the timestamp
          'unit': 'kWh',
        }
      }
      return jsonify(consumption_data), 200, {'Content-Type': 'application/json'}
    except Exception as e:
      logger.error(f'Failed to retrieve consumption data: {e}')
      return jsonify({'error': 'Failed to retrieve data'}), 500
