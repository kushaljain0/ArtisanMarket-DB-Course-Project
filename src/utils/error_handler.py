"""Centralized error handling for ArtisanMarket."""

import functools
import traceback
from typing import Any, Callable, Dict, Type, Union
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from .logger import get_logger

logger = get_logger(__name__)


class ArtisanMarketError(Exception):
    """Base exception for ArtisanMarket application."""

    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class DatabaseError(ArtisanMarketError):
    """Database-related errors."""

    pass


class ConnectionError(ArtisanMarketError):
    """Database connection errors."""

    pass


class ValidationError(ArtisanMarketError):
    """Data validation errors."""

    pass


class NotFoundError(ArtisanMarketError):
    """Resource not found errors."""

    pass


class AuthenticationError(ArtisanMarketError):
    """Authentication and authorization errors."""

    pass


class RateLimitError(ArtisanMarketError):
    """Rate limiting errors."""

    pass


class ServiceUnavailableError(ArtisanMarketError):
    """Service unavailable errors."""

    pass


def handle_errors(
    error_types: Union[Type[Exception], tuple] = Exception,
    default_return: Any = None,
    log_error: bool = True,
    reraise: bool = True,
):
    """Decorator to handle errors with logging and recovery options.

    Args:
        error_types: Exception types to catch
        default_return: Value to return on error (if not reraise)
        log_error: Whether to log the error
        reraise: Whether to reraise the exception
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_types as e:
                if log_error:
                    logger.error(
                        "Function error",
                        function=func.__name__,
                        error=str(e),
                        error_type=type(e).__name__,
                        traceback=traceback.format_exc(),
                    )

                if reraise:
                    raise
                else:
                    return default_return

        return wrapper

    return decorator


def retry_on_failure(
    max_attempts: int = 3,
    exceptions: tuple = (ConnectionError, DatabaseError),
    exponential_backoff: bool = True,
):
    """Decorator to retry operations on failure.

    Args:
        max_attempts: Maximum number of retry attempts
        exceptions: Exception types to retry on
        exponential_backoff: Whether to use exponential backoff
    """

    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=4, max=10)
            if exponential_backoff
            else None,
            retry=retry_if_exception_type(exceptions),
            before_sleep=before_sleep_log(logger, logger.level),
        )
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_input(validation_func: Callable, error_message: str = "Invalid input"):
    """Decorator to validate function inputs.

    Args:
        validation_func: Function that returns True if input is valid
        error_message: Error message for invalid input
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not validation_func(*args, **kwargs):
                raise ValidationError(error_message)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_connection(connection_check_func: Callable):
    """Decorator to ensure database connection is available.

    Args:
        connection_check_func: Function that checks connection status
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not connection_check_func():
                raise ConnectionError("Database connection not available")
            return func(*args, **kwargs)

        return wrapper

    return decorator


class ErrorContext:
    """Context manager for error handling with additional context."""

    def __init__(self, operation: str, context: Dict = None):
        self.operation = operation
        self.context = context or {}
        self.logger = get_logger(__name__)

    def __enter__(self):
        self.logger.info("Operation started", operation=self.operation, **self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.logger.info(
                "Operation completed", operation=self.operation, **self.context
            )
        else:
            self.logger.error(
                "Operation failed",
                operation=self.operation,
                error=str(exc_val),
                error_type=exc_type.__name__,
                **self.context,
            )


def safe_execute(
    func: Callable,
    *args,
    default_return: Any = None,
    error_message: str = "Operation failed",
    **kwargs,
) -> Any:
    """Safely execute a function with error handling.

    Args:
        func: Function to execute
        default_return: Value to return on error
        error_message: Error message for logging
        *args, **kwargs: Arguments to pass to function

    Returns:
        Function result or default_return on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(
            "Safe execution failed",
            function=func.__name__,
            error=str(e),
            error_type=type(e).__name__,
            message=error_message,
        )
        return default_return


def create_error_response(
    error: Exception, include_traceback: bool = False
) -> Dict[str, Any]:
    """Create a standardized error response.

    Args:
        error: The exception that occurred
        include_traceback: Whether to include traceback in response

    Returns:
        Standardized error response dictionary
    """
    response = {
        "error": True,
        "message": str(error),
        "error_type": type(error).__name__,
    }

    if hasattr(error, "error_code"):
        response["error_code"] = error.error_code

    if hasattr(error, "details"):
        response["details"] = error.details

    if include_traceback:
        response["traceback"] = traceback.format_exc()

    return response


def is_retryable_error(error: Exception) -> bool:
    """Check if an error is retryable.

    Args:
        error: The exception to check

    Returns:
        True if the error is retryable
    """
    retryable_types = (
        ConnectionError,
        DatabaseError,
        ServiceUnavailableError,
        TimeoutError,
        OSError,
    )

    return isinstance(error, retryable_types)


def log_and_raise(error: Exception, message: str = None, context: Dict = None) -> None:
    """Log an error and raise it.

    Args:
        error: The exception to log and raise
        message: Additional message to log
        context: Additional context to log
    """
    log_data = {"error": str(error), "error_type": type(error).__name__}

    if message:
        log_data["message"] = message

    if context:
        log_data.update(context)

    logger.error("Error occurred", **log_data)
    raise error
