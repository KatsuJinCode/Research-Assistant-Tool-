"""
Core Backend Infrastructure

Provides error handling, logging, and utilities for the application.
"""

from .exceptions import (
    ApplicationError,
    ErrorCode,
    DatabaseError,
    DatabaseConnectionError,
    DocumentError,
    DocumentNotFoundError,
    DocumentUploadError,
    ClaimError,
    ClaimNotFoundError,
    ProjectError,
    ProjectNotFoundError,
    AIError,
    AIAPIError,
    ValidationError,
    MissingRequiredFieldError
)

from .error_handler import register_error_handlers, safe_execute, safe_execute_async
from .logging_config import setup_logging, get_logger, log_request, RequestContext

__all__ = [
    # Exceptions
    "ApplicationError",
    "ErrorCode",
    "DatabaseError",
    "DatabaseConnectionError",
    "DocumentError",
    "DocumentNotFoundError",
    "DocumentUploadError",
    "ClaimError",
    "ClaimNotFoundError",
    "ProjectError",
    "ProjectNotFoundError",
    "AIError",
    "AIAPIError",
    "ValidationError",
    "MissingRequiredFieldError",

    # Error handling
    "register_error_handlers",
    "safe_execute",
    "safe_execute_async",

    # Logging
    "setup_logging",
    "get_logger",
    "log_request",
    "RequestContext"
]
