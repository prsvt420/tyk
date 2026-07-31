from collections.abc import Callable
from logging import Filter, LogRecord, config
from time import gmtime, struct_time
from typing import Any, Literal, SupportsIndex

from pythonjsonlogger.core import RESERVED_ATTRS
from pythonjsonlogger.json import JsonFormatter

from src.infrastructure.context_vars import request_id_context_var


class _UTCJSONFormatter(JsonFormatter):
    """Format structured logs with UTC timestamps."""

    converter: Callable[[float | SupportsIndex | None], struct_time] = gmtime


class RequestContextVarsFilter(Filter):
    """Add request context vars to log records."""

    def filter(self, record: LogRecord) -> bool:
        """Add request context vars to a log record."""
        request_context_vars: dict[str, str | None] = {
            "request_id": request_id_context_var.get()
        }

        for context_var, value in request_context_vars.items():
            if value is not None:
                setattr(record, context_var, value)

        return True


def configure_logging(
    log_level: Literal[
        "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    ] = "INFO",
) -> None:
    """Configure app logging."""
    sqlalchemy_log_level: Literal["WARNING", "INFO"] = (
        "INFO" if log_level == "DEBUG" else "WARNING"
    )

    logging_config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_context": {
                "()": RequestContextVarsFilter,
            },
        },
        "formatters": {
            "default": {
                "()": _UTCJSONFormatter,
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%SZ",
                "rename_fields": {
                    "asctime": "timestamp",
                    "levelname": "level",
                    "name": "logger",
                },
                "reserved_attrs": [
                    *RESERVED_ATTRS,
                    "color_message",
                ],
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "filters": ["request_context"],
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "handlers": [
                "console",
            ],
            "level": log_level,
        },
        "loggers": {
            "uvicorn": {
                "handlers": [
                    "console",
                ],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": [
                    "console",
                ],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": [
                    "console",
                ],
                "level": log_level,
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": sqlalchemy_log_level,
                "propagate": True,
            },
            "sqlalchemy.pool": {
                "level": "WARNING",
                "propagate": True,
            },
            "sqlalchemy.orm": {
                "level": "WARNING",
                "propagate": True,
            },
            "asyncpg": {
                "level": "WARNING",
                "propagate": True,
            },
        },
    }

    config.dictConfig(config=logging_config)
