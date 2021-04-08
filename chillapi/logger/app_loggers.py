import logging
import sys

from chillapi.logger.formatter import GelfFormatter

allowed_reserved_attrs = [
    "levelname",
    "name",
]

formatter = GelfFormatter(allowed_reserved_attrs=allowed_reserved_attrs)

stout_handler = logging.StreamHandler(sys.stdout)
stout_handler.setLevel(logging.DEBUG)
stout_handler.setFormatter(formatter)

logger = logging.getLogger("app")
error_handler_logger = logging.getLogger("error_handler")
audit_logger = logging.getLogger("audit_logger")
logger.setLevel(logging.DEBUG)
error_handler_logger.setLevel(logging.DEBUG)
audit_logger.setLevel(logging.DEBUG)
logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)

logger.addHandler(stout_handler)
error_handler_logger.addHandler(stout_handler)
audit_logger.addHandler(stout_handler)
logging.getLogger("sqlalchemy.engine").addHandler(stout_handler)


def set_logger_config(logger_config: dict):
    log_file_handler = None
    for logger_name, config in logger_config.items():
        if logger_name == "sqlalchemy":
            logger_name = "sqlalchemy.engine"

        if "output" in config and config["output"] == "null":
            log_null_handler = logging.NullHandler()
            logging.getLogger(logger_name).removeHandler(stout_handler)
            logging.getLogger(logger_name).addHandler(log_null_handler)
            continue
        if "output" in config and config["output"] not in ["stdout", "null"]:
            if log_file_handler is None:
                log_file_handler = logging.FileHandler(config["output"])
                log_file_handler.setFormatter(formatter)
            logging.getLogger(logger_name).removeHandler(stout_handler)
            logging.getLogger(logger_name).addHandler(log_file_handler)
            continue
        if "level" in config:
            logging.getLogger(logger_name).setLevel(int(config["level"]))
