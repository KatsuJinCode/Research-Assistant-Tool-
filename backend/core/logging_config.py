"""
Structured Logging Configuration

Configures application-wide logging with structured format,
rotation, and different levels for different components.
"""

import logging
import logging.handlers
import json
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.

    Outputs logs in JSON format with consistent fields:
    - timestamp: ISO format timestamp
    - level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - logger: Logger name
    - message: Log message
    - extra: Any extra fields passed to log
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName",
                "relativeCreated", "thread", "threadName", "exc_info",
                "exc_text", "stack_info", "taskName"
            ]:
                log_data[key] = value

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for better readability.

    Uses ANSI color codes to color log levels:
    - DEBUG: Cyan
    - INFO: Green
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Red background
    """

    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[41m',   # Red background
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        # Color the level name
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}"
                f"{record.levelname:8}"
                f"{self.RESET}"
            )

        return super().format(record)


def setup_logging(
    app_name: str = "research_assistant",
    log_level: str = "INFO",
    log_dir: str = "logs",
    enable_json: bool = False,
    enable_console: bool = True,
    enable_file: bool = True
) -> logging.Logger:
    """
    Configure application-wide logging.

    Args:
        app_name: Name of the application
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        enable_json: Enable JSON formatting for file logs
        enable_console: Enable console logging
        enable_file: Enable file logging

    Returns:
        Configured root logger
    """

    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)

        # Use colored formatter for console
        console_formatter = ColoredFormatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # File handler with rotation
    if enable_file:
        # Main application log
        app_log_file = log_path / f"{app_name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)

        # Use JSON or standard formatter
        if enable_json:
            file_formatter = JSONFormatter()
        else:
            file_formatter = logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # Error log (only ERROR and CRITICAL)
        error_log_file = log_path / f"{app_name}_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)

        if enable_json:
            error_formatter = JSONFormatter()
        else:
            error_formatter = logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s\n%(pathname)s:%(lineno)d\n%(message)s\n",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        error_handler.setFormatter(error_formatter)
        root_logger.addHandler(error_handler)

    # Configure specific loggers
    configure_logger_levels()

    root_logger.info(f"Logging configured for {app_name} at level {log_level}")

    return root_logger


def configure_logger_levels():
    """Configure log levels for specific modules"""

    # Set quieter levels for noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.INFO)
    logging.getLogger("neo4j").setLevel(logging.WARNING)
    logging.getLogger("socketio").setLevel(logging.INFO)
    logging.getLogger("engineio").setLevel(logging.WARNING)

    # Application loggers
    logging.getLogger("backend.database").setLevel(logging.DEBUG)
    logging.getLogger("backend.agents").setLevel(logging.INFO)
    logging.getLogger("backend.ml").setLevel(logging.INFO)
    logging.getLogger("backend.nlp").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger
    """
    return logging.getLogger(name)


# Request logging decorator
def log_request(logger: logging.Logger):
    """
    Decorator to log function calls with parameters and results.

    Usage:
        @log_request(logger)
        def my_function(arg1, arg2):
            ...
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(
                f"Calling {func.__name__}",
                extra={
                    "function": func.__name__,
                    "args": str(args)[:200],  # Truncate long args
                    "kwargs": str(kwargs)[:200]
                }
            )

            try:
                result = func(*args, **kwargs)
                logger.debug(
                    f"Completed {func.__name__}",
                    extra={"function": func.__name__}
                )
                return result
            except Exception as e:
                logger.error(
                    f"Error in {func.__name__}: {str(e)}",
                    exc_info=True,
                    extra={"function": func.__name__}
                )
                raise

        return wrapper
    return decorator


# Context logger for request tracking
class RequestContext:
    """
    Context manager for request-scoped logging.

    Usage:
        with RequestContext("user_123", "req_456"):
            logger.info("Processing request")
    """

    def __init__(self, user_id: str = None, request_id: str = None):
        self.user_id = user_id
        self.request_id = request_id
        self.filter = None

    def __enter__(self):
        """Add context to all logs"""
        self.filter = RequestContextFilter(self.user_id, self.request_id)
        logging.getLogger().addFilter(self.filter)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Remove context filter"""
        logging.getLogger().removeFilter(self.filter)


class RequestContextFilter(logging.Filter):
    """Filter to add request context to log records"""

    def __init__(self, user_id: str = None, request_id: str = None):
        super().__init__()
        self.user_id = user_id
        self.request_id = request_id

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context fields to record"""
        if self.user_id:
            record.user_id = self.user_id
        if self.request_id:
            record.request_id = self.request_id
        return True
