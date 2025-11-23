"""
Custom Exception Classes

Centralized exception handling for the Research Assistant Tool.
Provides user-friendly error messages and proper HTTP status codes.
"""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(Enum):
    """Standard error codes for the application"""
    # Database errors (1000-1999)
    DATABASE_CONNECTION_ERROR = 1000
    DATABASE_QUERY_ERROR = 1001
    DATABASE_TRANSACTION_ERROR = 1002
    DATABASE_CONSTRAINT_ERROR = 1003

    # Document errors (2000-2999)
    DOCUMENT_NOT_FOUND = 2000
    DOCUMENT_UPLOAD_ERROR = 2001
    DOCUMENT_PARSE_ERROR = 2002
    DOCUMENT_TOO_LARGE = 2003
    UNSUPPORTED_FILE_TYPE = 2004

    # Claim errors (3000-3999)
    CLAIM_NOT_FOUND = 3000
    CLAIM_VALIDATION_ERROR = 3001
    CLAIM_DUPLICATE = 3002

    # Project errors (4000-4999)
    PROJECT_NOT_FOUND = 4000
    PROJECT_VALIDATION_ERROR = 4001
    PROJECT_ALREADY_EXISTS = 4002

    # AI/Agent errors (5000-5999)
    AI_API_ERROR = 5000
    AI_RATE_LIMIT = 5001
    AI_INVALID_RESPONSE = 5002
    AGENT_EXECUTION_ERROR = 5003
    AGENT_NOT_FOUND = 5004

    # Search errors (6000-6999)
    SEARCH_QUERY_ERROR = 6000
    SEARCH_TIMEOUT = 6001

    # Authentication/Authorization errors (7000-7999)
    UNAUTHORIZED = 7000
    FORBIDDEN = 7001
    INVALID_CREDENTIALS = 7002

    # Validation errors (8000-8999)
    INVALID_INPUT = 8000
    MISSING_REQUIRED_FIELD = 8001
    INVALID_FORMAT = 8002

    # System errors (9000-9999)
    INTERNAL_ERROR = 9000
    SERVICE_UNAVAILABLE = 9001
    TIMEOUT = 9002


class ApplicationError(Exception):
    """
    Base exception class for all application errors.

    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code
        status_code: HTTP status code
        details: Additional error context
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON responses"""
        return {
            "error": True,
            "message": self.message,
            "error_code": self.error_code.value,
            "error_name": self.error_code.name,
            "status_code": self.status_code,
            "details": self.details
        }


# Database Exceptions
class DatabaseError(ApplicationError):
    """Base class for database-related errors"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.DATABASE_QUERY_ERROR,
            status_code=500,
            details=details
        )


class DatabaseConnectionError(DatabaseError):
    """Database connection failed"""

    def __init__(self, details: Optional[Dict] = None):
        super().__init__(
            message="Failed to connect to database. Please try again later.",
            details=details
        )
        self.error_code = ErrorCode.DATABASE_CONNECTION_ERROR


class DatabaseConstraintError(DatabaseError):
    """Database constraint violation"""

    def __init__(self, constraint: str, details: Optional[Dict] = None):
        super().__init__(
            message=f"Database constraint violation: {constraint}",
            details=details
        )
        self.error_code = ErrorCode.DATABASE_CONSTRAINT_ERROR
        self.status_code = 400


# Document Exceptions
class DocumentError(ApplicationError):
    """Base class for document-related errors"""

    def __init__(self, message: str, error_code: ErrorCode, status_code: int = 400, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details
        )


class DocumentNotFoundError(DocumentError):
    """Document not found"""

    def __init__(self, document_id: str):
        super().__init__(
            message=f"Document '{document_id}' not found",
            error_code=ErrorCode.DOCUMENT_NOT_FOUND,
            status_code=404,
            details={"document_id": document_id}
        )


class DocumentUploadError(DocumentError):
    """Document upload failed"""

    def __init__(self, reason: str, details: Optional[Dict] = None):
        super().__init__(
            message=f"Failed to upload document: {reason}",
            error_code=ErrorCode.DOCUMENT_UPLOAD_ERROR,
            status_code=400,
            details=details
        )


class DocumentParseError(DocumentError):
    """Document parsing failed"""

    def __init__(self, filename: str, reason: str):
        super().__init__(
            message=f"Failed to parse document '{filename}': {reason}",
            error_code=ErrorCode.DOCUMENT_PARSE_ERROR,
            status_code=422,
            details={"filename": filename, "reason": reason}
        )


class DocumentTooLargeError(DocumentError):
    """Document exceeds size limit"""

    def __init__(self, size: int, max_size: int):
        super().__init__(
            message=f"Document size ({size} bytes) exceeds maximum allowed size ({max_size} bytes)",
            error_code=ErrorCode.DOCUMENT_TOO_LARGE,
            status_code=413,
            details={"size": size, "max_size": max_size}
        )


class UnsupportedFileTypeError(DocumentError):
    """File type not supported"""

    def __init__(self, file_type: str, supported_types: list):
        super().__init__(
            message=f"File type '{file_type}' is not supported. Supported types: {', '.join(supported_types)}",
            error_code=ErrorCode.UNSUPPORTED_FILE_TYPE,
            status_code=415,
            details={"file_type": file_type, "supported_types": supported_types}
        )


# Claim Exceptions
class ClaimError(ApplicationError):
    """Base class for claim-related errors"""

    def __init__(self, message: str, error_code: ErrorCode, status_code: int = 400, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details
        )


class ClaimNotFoundError(ClaimError):
    """Claim not found"""

    def __init__(self, claim_id: str):
        super().__init__(
            message=f"Claim '{claim_id}' not found",
            error_code=ErrorCode.CLAIM_NOT_FOUND,
            status_code=404,
            details={"claim_id": claim_id}
        )


class ClaimValidationError(ClaimError):
    """Claim validation failed"""

    def __init__(self, reason: str, details: Optional[Dict] = None):
        super().__init__(
            message=f"Claim validation failed: {reason}",
            error_code=ErrorCode.CLAIM_VALIDATION_ERROR,
            status_code=400,
            details=details
        )


# Project Exceptions
class ProjectError(ApplicationError):
    """Base class for project-related errors"""

    def __init__(self, message: str, error_code: ErrorCode, status_code: int = 400, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details
        )


class ProjectNotFoundError(ProjectError):
    """Project not found"""

    def __init__(self, project_id: str):
        super().__init__(
            message=f"Project '{project_id}' not found",
            error_code=ErrorCode.PROJECT_NOT_FOUND,
            status_code=404,
            details={"project_id": project_id}
        )


class ProjectAlreadyExistsError(ProjectError):
    """Project already exists"""

    def __init__(self, project_name: str):
        super().__init__(
            message=f"Project '{project_name}' already exists",
            error_code=ErrorCode.PROJECT_ALREADY_EXISTS,
            status_code=409,
            details={"project_name": project_name}
        )


# AI/Agent Exceptions
class AIError(ApplicationError):
    """Base class for AI-related errors"""

    def __init__(self, message: str, error_code: ErrorCode, status_code: int = 500, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details
        )


class AIAPIError(AIError):
    """AI API call failed"""

    def __init__(self, provider: str, reason: str):
        super().__init__(
            message=f"AI API error ({provider}): {reason}",
            error_code=ErrorCode.AI_API_ERROR,
            status_code=502,
            details={"provider": provider, "reason": reason}
        )


class AIRateLimitError(AIError):
    """AI API rate limit exceeded"""

    def __init__(self, provider: str, retry_after: Optional[int] = None):
        super().__init__(
            message=f"AI API rate limit exceeded ({provider}). Please try again later.",
            error_code=ErrorCode.AI_RATE_LIMIT,
            status_code=429,
            details={"provider": provider, "retry_after": retry_after}
        )


class AgentExecutionError(AIError):
    """Agent execution failed"""

    def __init__(self, agent_name: str, reason: str):
        super().__init__(
            message=f"Agent '{agent_name}' execution failed: {reason}",
            error_code=ErrorCode.AGENT_EXECUTION_ERROR,
            status_code=500,
            details={"agent_name": agent_name, "reason": reason}
        )


# Search Exceptions
class SearchError(ApplicationError):
    """Base class for search-related errors"""

    def __init__(self, message: str, error_code: ErrorCode, status_code: int = 400, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details
        )


class SearchQueryError(SearchError):
    """Invalid search query"""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Invalid search query: {reason}",
            error_code=ErrorCode.SEARCH_QUERY_ERROR,
            status_code=400,
            details={"reason": reason}
        )


# Validation Exceptions
class ValidationError(ApplicationError):
    """Base class for validation errors"""

    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict] = None):
        details = details or {}
        if field:
            details["field"] = field

        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_INPUT,
            status_code=400,
            details=details
        )


class MissingRequiredFieldError(ValidationError):
    """Required field is missing"""

    def __init__(self, field: str):
        super().__init__(
            message=f"Required field '{field}' is missing",
            field=field
        )
        self.error_code = ErrorCode.MISSING_REQUIRED_FIELD


class InvalidFormatError(ValidationError):
    """Invalid data format"""

    def __init__(self, field: str, expected_format: str, actual_value: Any = None):
        details = {"expected_format": expected_format}
        if actual_value is not None:
            details["actual_value"] = str(actual_value)

        super().__init__(
            message=f"Invalid format for field '{field}'. Expected: {expected_format}",
            field=field,
            details=details
        )
        self.error_code = ErrorCode.INVALID_FORMAT


# System Exceptions
class ServiceUnavailableError(ApplicationError):
    """Service temporarily unavailable"""

    def __init__(self, service: str, reason: Optional[str] = None):
        message = f"Service '{service}' is temporarily unavailable"
        if reason:
            message += f": {reason}"

        super().__init__(
            message=message,
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            status_code=503,
            details={"service": service, "reason": reason}
        )


class TimeoutError(ApplicationError):
    """Operation timed out"""

    def __init__(self, operation: str, timeout: int):
        super().__init__(
            message=f"Operation '{operation}' timed out after {timeout} seconds",
            error_code=ErrorCode.TIMEOUT,
            status_code=408,
            details={"operation": operation, "timeout": timeout}
        )
