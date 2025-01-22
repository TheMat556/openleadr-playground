from flask import Flask, jsonify
from datetime import datetime

import threading

from src.adr_node.communication.rest.domain.domain import NodeStatus, ApiResponse
from src.adr_node.communication.rest.exceptions.rest import (
  ServiceStartupError,
  ServiceShutdownError,
)
from src.adr_node.communication.rest.interfaces.irest_service import IRestService
from src.adr_node.database.services.consumption_service import ConsumptionService
from src.adr_node.database.services.load_profile_service import LoadProfileService
from src.openadr_node import logger


class RestService(IRestService):
  def __init__(
    self,
    host: str,
    port: int,
    load_profile_service: LoadProfileService,
    consumption_service: ConsumptionService,
  ):
    self.host = host
    self.port = port
    self.app = Flask(__name__)
    self.server = None
    self._setup_routes()
    print('load_profile_service', load_profile_service)
    print('consumption_service', consumption_service)
    logger.info('REST service initialized successfully')

  def _setup_routes(self):
    @self.app.route('/api/status')
    def get_status():
      status = NodeStatus(
        node_id='node-001',
        status='running',
        last_updated=datetime.utcnow(),
        uptime=123.45,
        version='1.0.0',
      )

      response = ApiResponse(
        status='success', timestamp=datetime.utcnow(), data=status.__dict__
      )

      return jsonify(response.__dict__)

  def start(self) -> None:
    try:
      logger.info(f'Starting REST service on {self.host}:{self.port}')
      self.server = threading.Thread(
        target=self.app.run, kwargs={'host': self.host, 'port': self.port}
      )
      self.server.daemon = True
      self.server.start()
      logger.info('REST service started successfully')
    except Exception as e:
      error_msg = f'Failed to start REST service: {str(e)}'
      logger.error(error_msg)
      raise ServiceStartupError(error_msg)

  def stop(self) -> None:
    try:
      if self.server and self.server.is_alive():
        # Implement proper Flask shutdown
        pass
    except Exception as e:
      raise ServiceShutdownError(f'Failed to stop REST service: {str(e)}')
