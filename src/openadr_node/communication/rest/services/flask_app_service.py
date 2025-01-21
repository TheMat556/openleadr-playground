from flask import Flask, jsonify
from werkzeug.serving import make_server
from injector import inject

from src.openadr_node import logger
from src.openadr_node.communication.rest.interfaces.iflask_app_service import (
  IFlaskAppService,
)
from src.openadr_node.communication.rest.interfaces.irest_service import IRestService

from src.openadr_node.communication.rest.routes.consumption import consumption_bp
from src.openadr_node.communication.rest.routes.load_profile import load_profile_bp


class FlaskAppService(IFlaskAppService):
  @inject
  def __init__(self, rest_service: IRestService, port: int):
    self.port = port
    self._server = None

    # Initialize Flask app
    self.app = Flask('openadr_node')

    # Add application context
    self.app.config.update(
      REST_SERVICE=rest_service,
      STARTUP_TIME='2025-01-21 17:36:10',
      CURRENT_USER='TheMat556',
    )

    self.app.register_blueprint(load_profile_bp)
    self.app.register_blueprint(consumption_bp)

    # Register error handler
    @self.app.errorhandler(Exception)
    def handle_exception(e):
      return jsonify(
        {
          'error': str(e),
          'timestamp': self.app.config['STARTUP_TIME'],
          'user': self.app.config['CURRENT_USER'],
        }
      ), 500

  def serve_forever(self) -> None:
    """Start the Flask server"""
    try:
      if self._server is None:
        print(f'!!Starting Flask server on port {self.port}')
        self._server = make_server('0.0.0.0', self.port, self.app)
      self._server.serve_forever()
    except Exception as e:
      logger.error(f'Failed to start Flask server: {e}')
      raise

  def shutdown(self) -> None:
    """Shutdown the Flask server"""
    if self._server:
      logger.info('Shutting down Flask server...')
      self._server.shutdown()
      self._server = None
      logger.info('Flask server shut down successfully')
