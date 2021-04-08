from abc import abstractmethod
from datetime import datetime

from chillapi.exceptions.api_manager import ConfigError
from chillapi.http.utils import get_request_id, get_traced_request_uuid
from chillapi.logger.app_loggers import audit_logger


class AuditLog():
    request_id = None
    prev_request_id = None
    date = None

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

class AuditLogHandler:
    @abstractmethod
    def log(self, audit_log: AuditLog):
        pass

def register_audit_handler(app, audit_logger_package):
    audit_logger_handler = None
    audit_logger_handler_module = __import__(audit_logger_package['package'], fromlist=[
        audit_logger_package['audit_log_handler']]) if audit_logger_package is not None else None
    if audit_logger_handler_module is not None:
        audit_logger_handler_class = getattr(audit_logger_handler_module, audit_logger_package['audit_log_handler'])
        try:
            audit_logger_handler = audit_logger_handler_class(**audit_logger_package[
                'audit_log_handler_args'] if 'audit_log_handler_args' in audit_logger_package else {})
        except TypeError as e:
            raise ConfigError(f'{audit_logger_handler_class}: {e}')
        if not issubclass(audit_logger_handler_class, AuditLogHandler):
            raise ConfigError(
                f"{audit_logger_package['package']}.{audit_logger_package['audit_log_handler']} is not a sub class of {AuditLogHandler.__module__}")

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
