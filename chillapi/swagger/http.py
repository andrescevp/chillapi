import abc

import flask
from flask import jsonify, make_response

from chillapi.app.flask_restful_swagger_3 import Resource, Schema
from chillapi.extensions.audit import AuditLog
from chillapi.logger.app_loggers import logger
from chillapi.swagger import AfterResponseEventType, BeforeRequestEventType, BeforeResponseEventType


class ResourceResponse:
    response = {}
    headers: dict = {}
    http_code = 200
    audit = None

    def make_audit_log(self, **args):
        self.audit = AuditLog(**args)

    def make_response(self, as_json: bool = True):
        data = jsonify(self.response) if as_json else self.response
        response = make_response(data, self.http_code)
        if self.headers:
            for key, value in self.headers.items():
                response.headers[key] = value

        response.audit = self.audit

        return response

    def for_json(self) -> dict:
        return {
            "response": self.response,
            "headers": self.headers,
            "http_code": self.http_code,
        }


class AutomaticResource(Resource):
    route = "/"
    endpoint = "root"
    _swagger_schema: Schema = None
    before_request: BeforeRequestEventType = None
    before_response: BeforeResponseEventType = None
    db_table: dict = None

    def __init__(
        self,
        before_request: BeforeRequestEventType = None,
        before_response: BeforeResponseEventType = None,
        after_response: AfterResponseEventType = None,
    ):
        self.before_response = before_response
        self.before_request = before_request

        if after_response:

            @flask.after_this_request
            def response_processor(response):
                after_response.on_event(**{"resource": self, "response": response})
                return response

    @abc.abstractmethod
    def request(self, **args) -> ResourceResponse:
        pass

    @abc.abstractmethod
    def validate_request(self, **args):
        pass

    def process_request(self, **args):
        logger.debug("Request start", extra=args)
        before_response_event = None
        before_request_event = None

        request_args = {**args, **{"before_request_event": before_request_event, "before_response_event": before_response_event}}

        if self.before_request:
            logger.debug("Before request event trigger", extra=request_args)

            before_request_event = self.before_request.on_event(**{"resource": self}, **request_args)

            request_args["before_request_event"] = before_request_event

        logger.debug("Validate request event trigger", extra={**request_args})

        validation_output = self.validate_request(**request_args)

        request_args["validation_output"] = validation_output

        response = self.request(**request_args)

        if self.before_response:
            logger.debug("Before response event trigger", extra=request_args)

            before_response_event = self.before_response.on_event(
                **{
                    "resource": self,
                    "response": response,
                },
                **request_args,
            )

            request_args["before_response_event"] = before_response_event

        request_args["response"] = response
        logger.debug("Response finish", extra=request_args)

        return response.make_response()
