from flask import Blueprint, make_response
from flask_api import status
from flask_cors import CORS

from backend.config import Config
from backend.endpoints.util import handle_exceptions, log_request

device_bp = Blueprint('device_blueprint', __name__)
CORS(device_bp)


@device_bp.route(
    "/discover", methods=['GET'], endpoint='discover'
)
@handle_exceptions
@log_request
def route_discover():
    return make_response((
        {'device_id': Config.get_value('device_id')},
        status.HTTP_200_OK
    ))
