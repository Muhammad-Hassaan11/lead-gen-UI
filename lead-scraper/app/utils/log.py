"""structlog config + module-level logger."""
from __future__ import annotations

import logging

import structlog
from structlog.typing import Processor


def configure_logging(log_level: str = "INFO") -> None:
    normalized_level = log_level.upper()
    level = getattr(logging, normalized_level, logging.INFO)
    renderer: Processor

    if normalized_level == "DEBUG":
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        renderer = structlog.processors.JSONRenderer()

    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        renderer,
    ]

    logging.basicConfig(level=level, format="%(message)s")
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


logger = structlog.get_logger("prospector")
