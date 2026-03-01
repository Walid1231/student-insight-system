"""
Security utilities — JWT error handlers, role enforcement.

Called once during app factory setup:
    from core.security import register_jwt_handlers
    register_jwt_handlers(jwt)
"""

from functools import wraps
from flask import request, redirect, url_for, jsonify, abort
from flask_jwt_extended import verify_jwt_in_request, get_jwt


# ── JWT Error Handlers ────────────────────────────────────────────

def _is_browser_request():
    """Return True if this is a browser page request (not XHR/API)."""
    accept = request.headers.get("Accept", "")
    return "text/html" in accept


def register_jwt_handlers(jwt):
    """Attach JWT error handlers that redirect browsers to login."""

    @jwt.unauthorized_loader
    def missing_token_callback(reason):
        if _is_browser_request():
            return redirect(url_for("auth.logout"))
        return jsonify({"msg": reason}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        if _is_browser_request():
            return redirect(url_for("auth.logout"))
        return jsonify({"msg": reason}), 422

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        if _is_browser_request():
            return redirect(url_for("auth.logout"))
        return jsonify({"msg": "Token has expired"}), 401

    @jwt.needs_fresh_token_loader
    def needs_fresh_token_callback(jwt_header, jwt_payload):
        if _is_browser_request():
            return redirect(url_for("auth.logout"))
        return jsonify({"msg": "Fresh token required"}), 401


# ── Role Enforcement Decorator ────────────────────────────────────

def require_role(*allowed_roles):
    """
    Decorator that enforces JWT authentication AND role membership.

    Usage:
        @app.route("/student/dashboard")
        @require_role("student")
        def student_dashboard():
            ...

        @app.route("/admin/panel")
        @require_role("teacher", "admin")
        def admin_panel():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            role = claims.get("role")
            if role not in allowed_roles:
                if _is_browser_request():
                    abort(403)
                return jsonify({"msg": "Access denied"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
