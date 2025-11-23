"""
Error Handler Middleware

Centralized error handling for Flask application.
Converts exceptions to consistent JSON responses.
"""

import logging
import traceback
from typing import Tuple, Dict, Any
from flask import jsonify, request
from werkzeug.exceptions import HTTPException

from .exceptions import ApplicationError, ErrorCode

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """
    Register error handlers with Flask application.

    Args:
        app: Flask application instance
    """

    @app.errorhandler(ApplicationError)
    def handle_application_error(error: ApplicationError) -> Tuple[Dict, int]:
        """Handle custom application errors"""
        logger.error(
            f"Application error: {error.message}",
            extra={
                "error_code": error.error_code.name,
                "status_code": error.status_code,
                "details": error.details,
                "path": request.path,
                "method": request.method
            }
        )

        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException) -> Tuple[Dict, int]:
        """Handle standard HTTP exceptions"""
        logger.warning(
            f"HTTP error {error.code}: {error.description}",
            extra={
                "status_code": error.code,
                "path": request.path,
                "method": request.method
            }
        )

        return jsonify({
            "error": True,
            "message": error.description,
            "status_code": error.code
        }), error.code

    @app.errorhandler(ValueError)
    def handle_value_error(error: ValueError) -> Tuple[Dict, int]:
        """Handle ValueError (validation errors)"""
        logger.warning(
            f"Validation error: {str(error)}",
            extra={
                "path": request.path,
                "method": request.method
            }
        )

        return jsonify({
            "error": True,
            "message": str(error),
            "error_code": ErrorCode.INVALID_INPUT.value,
            "status_code": 400
        }), 400

    @app.errorhandler(Exception)
    def handle_generic_exception(error: Exception) -> Tuple[Dict, int]:
        """Handle unexpected exceptions"""
        # Log full traceback for debugging
        logger.error(
            f"Unexpected error: {str(error)}",
            exc_info=True,
            extra={
                "path": request.path,
                "method": request.method,
                "traceback": traceback.format_exc()
            }
        )

        # Don't expose internal error details in production
        return jsonify({
            "error": True,
            "message": "An unexpected error occurred. Please try again later.",
            "error_code": ErrorCode.INTERNAL_ERROR.value,
            "status_code": 500
        }), 500

    @app.errorhandler(404)
    def handle_not_found(error) -> Tuple[Dict, int]:
        """Handle 404 Not Found"""
        logger.info(
            f"Resource not found: {request.path}",
            extra={
                "path": request.path,
                "method": request.method
            }
        )

        return jsonify({
            "error": True,
            "message": f"Resource not found: {request.path}",
            "status_code": 404
        }), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error) -> Tuple[Dict, int]:
        """Handle 405 Method Not Allowed"""
        logger.warning(
            f"Method not allowed: {request.method} {request.path}",
            extra={
                "path": request.path,
                "method": request.method
            }
        )

        return jsonify({
            "error": True,
            "message": f"Method {request.method} not allowed for {request.path}",
            "status_code": 405
        }), 405

    logger.info("Error handlers registered successfully")


def safe_execute(func, *args, error_message: str = "Operation failed", **kwargs) -> Any:
    """
    Safely execute a function with error handling.

    Args:
        func: Function to execute
        *args: Positional arguments for function
        error_message: Message to use if error occurs
        **kwargs: Keyword arguments for function

    Returns:
        Function result

    Raises:
        ApplicationError: If function execution fails
    """
    try:
        return func(*args, **kwargs)
    except ApplicationError:
        # Re-raise application errors
        raise
    except Exception as e:
        logger.error(f"{error_message}: {str(e)}", exc_info=True)
        raise ApplicationError(
            message=f"{error_message}: {str(e)}",
            error_code=ErrorCode.INTERNAL_ERROR,
            status_code=500,
            details={"original_error": str(e)}
        )


async def safe_execute_async(func, *args, error_message: str = "Operation failed", **kwargs) -> Any:
    """
    Safely execute an async function with error handling.

    Args:
        func: Async function to execute
        *args: Positional arguments for function
        error_message: Message to use if error occurs
        **kwargs: Keyword arguments for function

    Returns:
        Function result

    Raises:
        ApplicationError: If function execution fails
    """
    try:
        return await func(*args, **kwargs)
    except ApplicationError:
        # Re-raise application errors
        raise
    except Exception as e:
        logger.error(f"{error_message}: {str(e)}", exc_info=True)
        raise ApplicationError(
            message=f"{error_message}: {str(e)}",
            error_code=ErrorCode.INTERNAL_ERROR,
            status_code=500,
            details={"original_error": str(e)}
        )
