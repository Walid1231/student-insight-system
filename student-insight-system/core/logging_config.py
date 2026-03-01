"""
Structured logging configuration.

Provides request-correlated log output with request IDs,
path context, and configurable format.

Register in app factory:
    from core.logging_config import setup_logging
    setup_logging(app)
"""

import logging
import sys
from uuid import uuid4

from flask import g, request


class RequestFormatter(logging.Formatter):
    """Formatter that appends request context (ID, path) to every log line."""

    def format(self, record):
        try:
            record.request_id = getattr(g, "request_id", "-")
            record.path = request.path if request else "-"
        except RuntimeError:
            # Outside request context (e.g. startup, CLI commands)
            record.request_id = "-"
            record.path = "-"
        return super().format(record)


def setup_logging(app):
    """Configure structured logging for the application."""
    log_level = logging.DEBUG if app.debug else logging.INFO

    formatter = RequestFormatter(
        fmt=(
            "%(asctime)s | %(levelname)-8s | %(request_id)s "
            "| %(name)s | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)

    # Configure root logger
    root = logging.getLogger()
    root.setLevel(log_level)
    # Remove existing handlers to avoid duplicate output
    root.handlers.clear()
    root.addHandler(handler)

    # Silence noisy libraries
    logging.getLogger("werkzeug").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # ── Request ID middleware ──
    @app.before_request
    def inject_request_id():
        g.request_id = request.headers.get("X-Request-ID", str(uuid4())[:8])

    app.logger.info("Logging initialised at %s", logging.getLevelName(log_level))
