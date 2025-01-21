# src/openadr_node/protocols/rest/routes/consumption.py
from flask import Blueprint, jsonify

from src.openadr_node.communication.rest.exceptions.exceptions import (
  RestServiceException,
)
from src.openadr_node.communication.rest.services.rest_service import RestService

consumption_bp = Blueprint('consumption', __name__)


@consumption_bp.route('/data/consumption', methods=['GET'])
def get_consumption(rest_service: RestService):
  try:
    data, status_code = rest_service.get_current_consumption()
    return jsonify(data), status_code
  except RestServiceException as e:
    return jsonify(e.to_dict()), e.status_code
