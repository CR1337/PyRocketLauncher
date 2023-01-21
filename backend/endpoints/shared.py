from flask import (Blueprint, Response, make_response, redirect, request,
                   send_file, send_from_directory, url_for)
from flask_api import status
from flask_cors import CORS

from backend.config import Config
from backend.controller import Controller
from backend.endpoints.util import handle_exceptions, log_request
from backend.event_stream import EventStream
from backend.hardware import Hardware
from backend.instance import Instance
from backend.logger import logger
from backend.system import System

shared_bp = Blueprint('shared_blueprint', __name__)
CORS(shared_bp)


@shared_bp.route(
    "/", methods=['GET'], endpoint='index'
)
@handle_exceptions
@log_request
def route_index():
    System.check_for_update()
    path = f"{Instance.get_prefix()}.html"
    return redirect(url_for('static', filename=path))


@shared_bp.route(
    "/favicon.ico", methods=['GET'], endpoint='favicon'
)
@handle_exceptions
@log_request
def route_favicon():
    return redirect(url_for('static', filename='assets/favicon.ico'))


@shared_bp.route(
    '/static/<path:path>', methods=['GET'], endpoint='static'
)
@handle_exceptions
@log_request
def route_static(path):
    return make_response((
        send_from_directory('static', path),
        status.HTTP_200_OK
    ))


@shared_bp.route(
    "/program", methods=['POST', 'DELETE'], endpoint='program'
)
@handle_exceptions
@log_request
def route_program():
    if request.method == 'POST':
        json_data = request.get_json(force=True)
        Controller.load_program(json_data['name'], json_data['event_list'])
    elif request.method == 'DELETE':
        Controller.unload_program()

    return make_response((
        {}, status.HTTP_200_OK
    ))


@shared_bp.route(
    "/program/control", methods=['POST'], endpoint='program_control'
)
@handle_exceptions
@log_request
def route_program_control():
    action = request.get_json(force=True)['action']
    if action == 'run':
        Controller.run_program()
    elif action == 'pause':
        Controller.pause_program()
    elif action == 'continue':
        Controller.continue_program()
    elif action == 'stop':
        Controller.stop_program()
    elif action == 'schedule':
        time = request.get_json(force=True)['time']
        Controller.schedule_program(time)
    elif action == 'unschedule':
        Controller.unschedule_program()

    return make_response((
        {}, status.HTTP_200_OK
    ))


@shared_bp.route(
    "/fire", methods=['POST'], endpoint='fire'
)
@handle_exceptions
@log_request
def route_fire():
    json_data = request.get_json(force=True)
    if Instance.is_master():
        Controller.fire(
            json_data['device_id'], json_data['letter'], json_data['number']
        )
    else:
        Controller.fire(
            json_data['letter'], json_data['number']
        )
    return make_response((
        {}, status.HTTP_200_OK
    ))


@shared_bp.route(
    "/testloop", methods=['POST'], endpoint='testloop'
)
@handle_exceptions
@log_request
def route_testloop():
    Controller.run_testloop()
    return make_response((
        {}, status.HTTP_200_OK
    ))


@shared_bp.route(
    "/lock", methods=['POST'], endpoint='lock'
)
@handle_exceptions
@log_request
def route_lock():
    is_locked = request.get_json(force=True)['is_locked']
    if Instance.is_master():
        Controller.set_hardware_lock(is_locked)
    else:
        if is_locked:
            Hardware.lock()
        else:
            Hardware.unlock()
    return make_response((
        {}, status.HTTP_200_OK
    ))


@shared_bp.route(
    "/system-time", methods=['GET'], endpoint='system_time'
)
@handle_exceptions
@log_request
def route_system_time():
    return make_response((
        {'system_time': Controller.get_system_time()},
        status.HTTP_200_OK
    ))


@shared_bp.route(
    "/event-stream", methods=['GET'], endpoint='event_stream'
)
@handle_exceptions
@log_request
def route_event_stream():
    event_stream = EventStream()
    return Response(
        event_stream.event_stream_handler(),
        mimetype='text/event-stream'
    )


@shared_bp.route(
    "/state", methods=['GET'], endpoint='state'
)
@handle_exceptions
@log_request
def route_state():
    return make_response((
        Controller.get_state(),
        status.HTTP_200_OK
    ))


@shared_bp.route(
    "/logs", methods=['GET'], endpoint='logs'
)
@handle_exceptions
@log_request
def route_logs():
    return make_response((
        logger.get_log_files(),
        status.HTTP_200_OK
    ))


@shared_bp.route(
    "/logs/<filename>", methods=['GET'], endpoint='logs_filename'
)
@handle_exceptions
@log_request
def route_logs_filename(filename: str):
    if logger.logfile_exists(filename):
        return make_response((
            send_file(
                path_or_file=f"logs/{filename}",
                mimetype="text/plain",
                as_attachment=True
            ),
            status.HTTP_200_OK
        ))
    else:
        return make_response((
            {}, status.HTTP_404_NOT_FOUND
        ))


@shared_bp.route(
    "/logs/structured/<filename>", methods=['GET'],
    endpoint='logs_structured_filename'
)
@handle_exceptions
@log_request
def route_logs_structured_filename(filename: str):
    if logger.logfile_exists(filename):
        return make_response((
            logger.get_log_structured_file_content(filename),
            status.HTTP_200_OK
        ))
    else:
        return make_response((
            {}, status.HTTP_404_NOT_FOUND
        ))


@shared_bp.route(
    "/config", methods=['GET', 'POST'], endpoint='config'
)
@handle_exceptions
@log_request
def route_config():
    if request.method == 'GET':
        return make_response((
            Config.get_state(),
            status.HTTP_200_OK
        ))
    elif request.method == 'POST':
        Config.update_state(request.get_json(force=True))
        return make_response((
            {}, status.HTTP_200_OK
        ))


@shared_bp.route(
    "/update", methods=['POST'], endpoint='update'
)
@handle_exceptions
@log_request
def route_update():
    Controller.update()
    return make_response(({}, status.HTTP_200_OK))
