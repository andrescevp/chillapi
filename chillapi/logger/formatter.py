"""Logging formatter for Graylog Extended Log Format (GELF).

This module implements a custom formatter for the Python standard library `logging`_
module that conforms to the `GELF Payload Specification Version 1.1`_.

.. _logging:
   https://docs.python.org/3/library/logging.html

.. _GELF Payload Specification Version 1.1:
   http://docs.graylog.org/en/3.0/pages/gelf.html#gelf-payload-specification
"""

import logging
import socket
import types
from datetime import datetime

import simplejson

from chillapi.http.utils import get_request_id, get_traced_request_uuid
from chillapi.database.query_builder import sql_operators


class CustomEncoder(simplejson.JSONEncoder):
    def default(self, o):
        if isinstance(o, types.BuiltinFunctionType):
            if o in sql_operators.values():
                return sql_operators.keys()[sql_operators.values().index(o)]
            return o.__str__
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


GELF_VERSION = "1.1"
"""str: GELF specification version."""

GELF_LEVELS = {
    logging.DEBUG: 7,
    logging.INFO: 6,
    logging.WARNING: 4,
    logging.ERROR: 3,
    logging.CRITICAL: 2,
}
"""dict: Map of logging levels vs syslog levels."""

GELF_IGNORED_ATTRS = ["id"]
"""List[str]: Attributes prohibited by the GELF specification."""

RESERVED_ATTRS = (
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
)
"""List[str]: The `logging.LogRecord`_ attributes that should be ignored by default.

.. _logging.LogRecord:
   https://docs.python.org/3/library/logging.html#logrecord-attributes
"""


def _prefix(str):
    """Prefixes a string with an underscore.

    Args:
        str (str): The string to prefix.

    Returns:
        str: The prefixed string.
    """
    return str if str.startswith("_") else "_%s" % str


def _prefix_reserved(str):
    """Prefixes a string with an underscore.

    Args:
        str (str): The string to prefix.

    Returns:
        str: The prefixed string.
    """
    if str == 'name':
        str = 'logger'
    return str if str.startswith("_") else "_%s" % str


class GelfFormatter(logging.Formatter):
    """A custom logging formatter for GELF.

    This formatter extends the Python standard library `logging.Formatter`_ and conforms
    to the GELF specification.

    Attributes:
        allowed_reserved_attrs: A list of reserved `logging.LogRecord`_ attributes that
        should not be ignored but rather included as additional fields.

        ignored_attrs: A list of additional attributes passed to a `logging.LogRecord`_
        via the `extra` keyword that will be ignored in addition to the reserved fields
        and not be present in the ouput.

    .. _logging.Formatter:
       https://docs.python.org/3/library/logging.html#logging.Formatter

    .. _logging.LogRecord:
       https://docs.python.org/3/library/logging.html#logrecord-attributes
    """

    def __init__(self, allowed_reserved_attrs=[], ignored_attrs=[]):
        """Initializes a GelfFormatter."""
        super().__init__()
        self.allowed_reserved_attrs = allowed_reserved_attrs
        self.ignored_attrs = ignored_attrs
        self._hostname = socket.gethostname()

    def format(self, record):
        """Formats a log record according to the GELF specification.

        Overrides `logging.Formatter.format`_.

        Args:
            record (logging.LogRecord): The original log record that should be formatted
                as a GELF log message.

        Returns:
            str: The serialized JSON GELF log message.

        .. _logging.Formatter.format:
           https://docs.python.org/3/library/logging.html#logging.Formatter.format
        """
        # Base GELF message structure
        request_uuid = get_request_id()
        traced_request_uuid = get_traced_request_uuid()
        log_record = dict(
            version=GELF_VERSION,
            short_message=record.getMessage(),
            timestamp=record.created,
            level=GELF_LEVELS[record.levelno],
            host=self._hostname,
            _request_uuid=request_uuid,
            _traced_request_uuid=traced_request_uuid,
        )

        # Capture exception info, if any
        if record.exc_info is not None:
            log_record["full_message"] = self.formatException(record.exc_info)

        # Set asctime field if required
        if "asctime" in self.allowed_reserved_attrs:
            record.asctime = self.formatTime(record)

        # Compute excluded attributes
        excluded_attrs = [
            x for x in RESERVED_ATTRS if x not in self.allowed_reserved_attrs
        ]
        excluded_attrs += self.ignored_attrs

        # Everything else is considered an additional attribute
        for key, value in record.__dict__.items():
            # if key in self.allowed_reserved_attrs:
            #     log_record[_prefix_reserved(key)] = value
            if key not in GELF_IGNORED_ATTRS and key not in excluded_attrs:
                if type(value) is datetime:
                    value = value.isoformat()
                log_record[_prefix(key)] = value

        # Serialize as JSON
        return simplejson.dumps(log_record, cls=CustomEncoder, for_json=True)
