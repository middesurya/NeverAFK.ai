"""
Structured JSON logging with correlation IDs for request tracing (PRD-013).

This module provides:
- StructuredFormatter: JSON formatter for structured logging
- StructuredLogger: Logger that supports extra structured fields
- Correlation ID management via context variables
- Sensitive field filtering for security
"""

import logging
import json
import sys
from datetime import datetime
from typing import Optional
from contextvars import ContextVar
import uuid

# Context variable for correlation ID - thread-safe and async-safe
correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='')


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging.

    Outputs log records as JSON objects with:
    - timestamp: ISO 8601 format with Z suffix
    - level: Log level name (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - message: Log message
    - logger: Logger name
    - module: Source module name
    - function: Source function name
    - line: Source line number
    - correlation_id: Request correlation ID (if set)
    - exception: Exception details with type, message, and traceback (if present)

    Sensitive fields (password, token, api_key, secret, authorization) are
    automatically filtered from extra_fields.
    """

    SENSITIVE_FIELDS = {'password', 'token', 'api_key', 'secret', 'authorization'}

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string.

        Args:
            record: The log record to format.

        Returns:
            JSON-formatted string representation of the log record.
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add correlation ID if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_entry['correlation_id'] = correlation_id

        # Add extra fields (filtering sensitive data)
        if hasattr(record, 'extra_fields') and record.extra_fields:
            for key, value in record.extra_fields.items():
                if key.lower() not in self.SENSITIVE_FIELDS:
                    log_entry[key] = value

        # Add exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info)
            }

        return json.dumps(log_entry)


class StructuredLogger(logging.Logger):
    """Logger that adds structured fields.

    Extends the standard Logger to support passing extra structured fields
    via the 'fields' keyword argument in log methods.

    Example:
        logger.info("User logged in", fields={'user_id': '123', 'action': 'login'})
    """

    def _log(self, level, msg, args, exc_info=None, extra=None, **kwargs):
        """Override to handle extra_fields from kwargs.

        Args:
            level: Log level
            msg: Log message
            args: Message arguments
            exc_info: Exception info tuple
            extra: Extra dict to be merged into LogRecord.__dict__
            **kwargs: Additional keyword arguments, including 'fields'
        """
        if extra is None:
            extra = {}

        # Support passing fields directly through extra dict
        if 'extra_fields' not in extra:
            extra['extra_fields'] = kwargs.get('fields', {})

        super()._log(level, msg, args, exc_info, extra)


def get_logger(name: str = None, level: str = 'INFO') -> logging.Logger:
    """Get a configured structured logger.

    Creates or returns a logger with the StructuredFormatter attached.
    Avoids duplicate handlers if called multiple times with the same name.

    Args:
        name: Logger name. Defaults to 'strong_mvp'.
        level: Log level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Case-insensitive. Defaults to 'INFO'.

    Returns:
        Configured logging.Logger instance.

    Example:
        logger = get_logger('my_module', level='DEBUG')
        logger.info("Message", extra={'extra_fields': {'key': 'value'}})
    """
    logging.setLoggerClass(StructuredLogger)

    logger = logging.getLogger(name or 'strong_mvp')
    logger.setLevel(getattr(logging, level.upper()))

    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)

    return logger


def set_correlation_id(correlation_id: str = None) -> str:
    """Set correlation ID for current context.

    Sets the correlation ID that will be included in all log messages
    within the current async context or thread.

    Args:
        correlation_id: Custom correlation ID. If None, a new UUID is generated.

    Returns:
        The correlation ID that was set.

    Example:
        cid = set_correlation_id()  # Generate new UUID
        cid = set_correlation_id("custom-123")  # Use custom ID
    """
    cid = correlation_id or str(uuid.uuid4())
    correlation_id_var.set(cid)
    return cid


def get_correlation_id() -> str:
    """Get current correlation ID.

    Returns:
        The current correlation ID, or empty string if not set.
    """
    return correlation_id_var.get()


# Default logger instance
logger = get_logger()
