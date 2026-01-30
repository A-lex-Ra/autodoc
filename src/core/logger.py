"""
Centralized logging configuration.

Objectives:
- Structured logging (JSON-first).
- Optional human-readable console output for development.
- Extensible hooks for future metrics integration.
- Thread-safe and idempotent initialization.
"""

import logging
import os
import json
import sys
from datetime import datetime
from typing import Optional

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "console").lower()  # "json" | "console"


class BaseMetricsHook:
    """
    Abstract base class for integrating metric recording with log events.
    """

    def emit(self, record: logging.LogRecord) -> None:
        return


_metrics_hook: Optional[BaseMetricsHook] = None


def set_metrics_hook(hook: BaseMetricsHook) -> None:
    global _metrics_hook
    _metrics_hook = hook


def _attach_metrics(record: logging.LogRecord) -> None:
    if _metrics_hook:
        try:
            _metrics_hook.emit(record)
        except Exception:
            pass


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }  # no extra fields printed

        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """
    Retrieves or configures a named logger instance.
    Safe to call repeatedly; prevents duplicate configuration.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(LOG_LEVEL)

    handler = logging.StreamHandler(sys.stdout)

    if LOG_FORMAT == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "<%(asctime)s> %(levelname)s [%(name)s] %(message)s"
            )
        )

    logger.addHandler(handler)

    class MetricsFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            _attach_metrics(record)
            return True

    logger.addFilter(MetricsFilter())
    logger.propagate = False
    return logger
