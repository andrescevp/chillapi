from datetime import datetime

from chillapi.app.config import table_extension
from chillapi.http.utils import get_request_id, get_traced_request_uuid
from chillapi.logger.app_loggers import audit_logger
from chillapi.abc import AuditLog as AuditLogBase, AuditLogHandler


class AuditLog(AuditLogBase):
    def __init__(self, message: str, action: str, change_parameters: dict, current_status: dict,
                 prev_status: dict = None,
                 user: str = None):
        self.action = action
        self.user = user
        self.prev_status = prev_status
        self.current_status = current_status
        self.change_parameters = change_parameters
        self.message = message

    def for_json(self) -> dict:
        return {
            'action': self.action,
            'user': self.user,
            'request_id': self.request_id,
            'prev_request_id': self.prev_request_id,
            'date': self.date,
            'change_parameters': self.change_parameters,
            'current_status': self.current_status,
            'prev_status': self.prev_status
        }

class NullAuditHandler(AuditLogHandler):
    pass

def register_audit_handler(app):
    audit_logger_handler = table_extension.get_extension('audit')

    @app.after_request
    def response_processor(response):
        # Prepare all the local variables you need since the request context
        # will be gone in the callback function
        log = None
        if 'audit' in response.__dict__ and isinstance(response.audit, AuditLog):
            log = response.audit
            log.request_id = get_request_id()
            log.prev_request_id = get_traced_request_uuid()
            log.date = datetime.now()

        @response.call_on_close
        def process_after_request():
            if log is not None:
                audit_logger.info(log.message, extra=log.for_json())
                if audit_logger_handler is not None:
                    audit_logger_handler.log(log)

        return response
