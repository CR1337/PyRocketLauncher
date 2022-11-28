import sys
import traceback

from flask import has_request_context, make_response, request
from flask_api import status

from backend.logger import logger
from backend.rl_exception import RlException


def _build_excpetion_response_content():
    exc_type, exc, tb = sys.exc_info()
    return {
        'exception_type': str(exc_type),
        'exception_args': vars(exc),
        'traceback': traceback.extract_tb(tb).format()
    }


def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
        except RlException:
            content = _build_excpetion_response_content()
            response = make_response(
                (content, status.HTTP_400_BAD_REQUEST)
            )
            logger.exception("RlException occured")
        except Exception:
            content = _build_excpetion_response_content()
            response = make_response(
                (content, status.HTTP_500_INTERNAL_SERVER_ERROR)
            )
            logger.exception("Unexpected Exception occured")
        finally:
            return response
    return wrapper


def log_request(func):
    def wrapper(*args, **kwargs):
        if has_request_context():
            logger.info(
                f"{request.method.capitalize()} request "
                f"to {request.endpoint} from {request.host}"
            )
        return func(*args, **kwargs)
    return wrapper
