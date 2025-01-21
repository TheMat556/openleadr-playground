from flask import Blueprint, jsonify

from src.openadr_node.communication.rest.exceptions.exceptions import (
  RestServiceException,
)
from src.openadr_node.communication.rest.services.rest_service import RestService

load_profile_bp = Blueprint('load_profile', __name__)


@load_profile_bp.route('/data/load_profile', methods=['GET'])
def get_load_profile(rest_service: RestService):
  try:
    data, status_code = rest_service.get_load_profile()
    return jsonify(data), status_code
  except RestServiceException as e:
    return jsonify(e.to_dict()), e.status_code
