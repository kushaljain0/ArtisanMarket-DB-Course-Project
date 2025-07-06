"""Centralized logging configuration for ArtisanMarket."""

import logging
import logging.config
import os
import sys
from pathlib import Path

import structlog
from structlog.stdlib import LoggerFactory


def setup_logging(
    log_level: str = "INFO", log_format: str = "json", log_file: str = None
) -> None:
    """Setup structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format (json, console)
        log_file: Optional log file path
    """

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
            if log_format == "json"
            else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Standard library logging configuration
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(),
            },
            "console": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(),
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": log_format,
                "stream": sys.stdout,
            },
        },
        "loggers": {
            "": {
                "handlers": ["console"],
                "level": log_level.upper(),
                "propagate": False,
            },
            "src": {
                "handlers": ["console"],
                "level": log_level.upper(),
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }

    # Add file handler if log_file is specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logging_config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "formatter": log_format,
            "filename": log_file,
        }

        # Add file handler to all loggers
        for logger_config in logging_config["loggers"].values():
            logger_config["handlers"].append("file")

    # Apply configuration
    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured structured logger
    """
    return structlog.get_logger(name)


def log_function_call(func):
    """Decorator to log function calls with parameters and results."""

    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)

        # Log function entry
        logger.info("Function called", function=func.__name__, args=args, kwargs=kwargs)

        try:
            result = func(*args, **kwargs)

            # Log successful completion
            logger.info(
                "Function completed",
                function=func.__name__,
                result_type=type(result).__name__,
            )

            return result

        except Exception as e:
            # Log error
            logger.error(
                "Function failed",
                function=func.__name__,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    return wrapper


def log_database_operation(operation: str, table: str = None, collection: str = None):
    """Decorator to log database operations."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)

            # Extract relevant info
            db_info = {
                "operation": operation,
                "table": table,
                "collection": collection,
                "function": func.__name__,
            }

            logger.info("Database operation started", **db_info)

            try:
                result = func(*args, **kwargs)

                logger.info("Database operation completed", **db_info, success=True)

                return result

            except Exception as e:
                logger.error(
                    "Database operation failed", **db_info, error=str(e), success=False
                )
                raise

        return wrapper

    return decorator


def log_performance(operation: str):
    """Decorator to log operation performance."""
    import time

    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)

            start_time = time.time()

            try:
                result = func(*args, **kwargs)

                duration = time.time() - start_time

                logger.info(
                    "Operation completed",
                    operation=operation,
                    function=func.__name__,
                    duration_ms=round(duration * 1000, 2),
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                logger.error(
                    "Operation failed",
                    operation=operation,
                    function=func.__name__,
                    duration_ms=round(duration * 1000, 2),
                    error=str(e),
                )
                raise

        return wrapper

    return decorator


# Initialize logging on module import
def init_logging():
    """Initialize logging with environment-based configuration."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_format = os.getenv("LOG_FORMAT", "json")
    log_file = os.getenv("LOG_FILE")

    setup_logging(log_level=log_level, log_format=log_format, log_file=log_file)


# Auto-initialize when module is imported
init_logging()
