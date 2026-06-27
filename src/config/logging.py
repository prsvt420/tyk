from logging import config
from pathlib import Path
from time import gmtime, struct_time
from typing import Any, Callable, Dict, SupportsIndex

from pythonjsonlogger.core import RESERVED_ATTRS
from pythonjsonlogger.json import JsonFormatter


class UTCJsonFormatter(JsonFormatter):
    """Format structured logs with UTC timestamps."""

    converter: Callable[[float | SupportsIndex | None], struct_time] = gmtime


def configure_logging(log_level: str = "INFO") -> None:
    """Configure application logging."""
    log_directory: Path = Path("logs")
    log_directory.mkdir(parents=True, exist_ok=True)

    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": UTCJsonFormatter,
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
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "default",
                "filename": log_directory / "app.log",
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 5,
                "encoding": "utf-8",
                "delay": True,
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": log_level,
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
        },
    }

    config.dictConfig(config=logging_config)
