import simplejson
import sqlalchemy
from flask import make_response
from werkzeug.exceptions import HTTPException
from wtforms import ValidationError

from chillapi.logger.app_loggers import error_handler_logger as logger


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException):
        response = e.get_response()
        # replace the body with JSON
        details = {"code": e.code, "description": f"{e.name}: {e.description}"}

        response.data = simplejson.dumps(details)

        response.content_type = "application/json"
        logger.error(e.description, extra={**details, **{"ex": str(e)}}, exc_info=True)
        return response

    @app.errorhandler(ValidationError)
    def handle_form_validation_exception(e: ValidationError):
        try:
            message = simplejson.loads(e.__str__())
        except Exception:
            message = e.__str__()

        response = {
            "code": 400,
            "description": message,
        }
        logger.error(message, extra={**response, **{"ex": str(e)}}, exc_info=True)
        return make_response(response, 400)

    @app.errorhandler(sqlalchemy.exc.DatabaseError)
    def handle_sqlalchemy_exception(e: sqlalchemy.exc.DatabaseError):
        message = e.__str__()

        if e.orig:
            message = e.orig.__str__()

        response = {
            "code": 500,
            "description": message,
        }

        logger.error(message, extra={**response, **{"ex": str(e)}}, exc_info=True)

        return make_response(response, 500)

    @app.errorhandler(Exception)
    def handle_exception(e):
        response = {
            "code": 500,
            "description": "Server Error",
        }
        logger.error("Server Error", extra={**response, **{"ex": str(e)}}, exc_info=True)
        return make_response(response, 500)
