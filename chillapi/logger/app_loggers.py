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


logger = logging.getLogger('app')
error_handler_logger = logging.getLogger('error_handler')
audit_logger = logging.getLogger('audit_logger')
logger.setLevel(logging.DEBUG)
error_handler_logger.setLevel(logging.DEBUG)
audit_logger.setLevel(logging.DEBUG)
logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

logger.addHandler(stout_handler)
error_handler_logger.addHandler(stout_handler)
audit_logger.addHandler(stout_handler)
logging.getLogger('sqlalchemy.engine').addHandler(stout_handler)
