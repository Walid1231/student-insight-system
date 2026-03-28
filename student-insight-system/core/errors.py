"""
Centralized error handling — custom exceptions + Flask error handler registration.

Usage in services:
    from core.errors import NotFoundError
    raise NotFoundError("Student profile not found")

Register in app factory:
    from core.errors import register_error_handlers
    register_error_handlers(app)
"""

import logging
from flask import jsonify, render_template, request

logger = logging.getLogger(__name__)


# ── Custom Exception Hierarchy ────────────────────────────────────

class AppError(Exception):
    """Base application error — all custom exceptions inherit from this."""
    status_code = 500
    default_message = "An internal error occurred"

    def __init__(self, message=None, payload=None):
        self.message = message or self.default_message
        self.payload = payload
        super().__init__(self.message)


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""
    status_code = 404
    default_message = "Resource not found"


class ValidationError(AppError):
    """Raised when input data fails validation."""
    status_code = 400
    default_message = "Invalid input"


class AuthorizationError(AppError):
    """Raised when a user lacks permission for an action."""
    status_code = 403
    default_message = "Access denied"


class ExternalServiceError(AppError):
    """Raised when an external service (AI, email, etc.) fails."""
    status_code = 502
    default_message = "External service unavailable"


class ConflictError(AppError):
    """Raised on duplicate / conflicting data operations."""
    status_code = 409
    default_message = "Resource conflict"


# ── Helpers ───────────────────────────────────────────────────────

def _wants_json():
    """Return True if the client prefers a JSON response."""
    accept = request.headers.get("Accept", "")
    is_xhr = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    return (
        "application/json" in accept
        or is_xhr
        or request.path.startswith("/api/")
    )


# ── Flask Error Handler Registration ─────────────────────────────

def register_error_handlers(app):
    """Call once in the app factory to register all error handlers."""

    @app.errorhandler(AppError)
    def handle_app_error(error):
        logger.warning(
            "AppError: %s (status=%d)", error.message, error.status_code
        )
        if _wants_json():
            resp = {"error": error.message}
            if error.payload:
                resp["details"] = error.payload
            return jsonify(resp), error.status_code
        # Browser — render a generic error template if it exists
        return _render_error(error.status_code, error.message)

    @app.errorhandler(404)
    def handle_404(error):
        if _wants_json():
            return jsonify({"error": "Not found"}), 404
        return _render_error(404, "Page not found")

    @app.errorhandler(500)
    def handle_500(error):
        logger.exception("Unhandled 500 error")
        if _wants_json():
            return jsonify({"error": "Internal server error"}), 500
        return _render_error(500, "Something went wrong")


def _render_error(code, message):
    """Try to render a specific error template, fall back to a simple page."""
    try:
        return render_template(f"errors/{code}.html"), code
    except Exception:
        # No template yet — return a minimal HTML page
        return (
            f"<h1>{code}</h1><p>{message}</p>"
            f"<a href='/'>← Back to home</a>"
        ), code
