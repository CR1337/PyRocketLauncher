import sys
import traceback

from backend.logger import logger
from flask import has_request_context, make_response, request
from flask_api import status


def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
        except Exception:
            print("EXCEPTION")
            exc_type, exc, tb = sys.exc_info()
            content = {
                'exception_type': str(exc_type),
                'exception_args': vars(exc),
                'traceback': traceback.extract_tb(tb).format()
            }
            response = make_response((content, status.HTTP_400_BAD_REQUEST))
            print("REQUEST", request)
            logger.exception("Exception occured")
        finally:
            return response
    return wrapper


def log_request(func):
    def wrapper(*args, **kwargs):
        if has_request_context():
            logger.info(f"{request.method.capitalize()} request to {request.endpoint} from {request.host}")
        return func(*args, **kwargs)
    return wrapper
