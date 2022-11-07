import json
from backend.controller import Controller
from flask import Blueprint, make_response, request
from flask_api import status

from backend.endpoints.util import handle_exceptions, log_request

master_bp = Blueprint('master_blueprint', __name__)


@master_bp.route("/search", methods=['GET'], endpoint='search')
@handle_exceptions
@log_request
def route_search():
    return make_response((
        Controller.search_devices(),
        status.HTTP_200_OK
    ))

@master_bp.route("/deregister", methods=['POST'], endpoint='deregister')
@handle_exceptions
@log_request
def route_deregister():
    json_data = request.get_json(force=True)
    device_id = json_data['device_id']
    Controller.deregister(device_id)
    return make_response((
        {'deregistered_device_id': device_id},
        status.HTTP_200_OK
    ))

@master_bp.route("/deregister-all", methods=['POST'], endpoint='deregister_all')
@handle_exceptions
@log_request
def route_deregister_all():
    Controller.deregister_all()
    return make_response(({}, status.HTTP_200_OK))

@master_bp.route("/devices", methods=['GET'], endpoint='devices')
@handle_exceptions
@log_request
def route_devices():
    devices = Controller.get_devices()
    return make_response((devices, status.HTTP_200_OK))
