"""
Application factory — single entry point for creating the Flask app.

Usage:
    from app import create_app
    app = create_app()             # defaults to DevelopmentConfig
    app = create_app("testing")    # uses TestingConfig
"""

import os
import time

from flask import Flask, render_template, request, redirect, url_for, jsonify

from config import config_by_name
from core.extensions import db, jwt, migrate, cors
from core.security import register_jwt_handlers
from core.errors import register_error_handlers
from core.logging_config import setup_logging


def create_app(config_name=None):
    """Create and configure the Flask application."""

    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Disable caching for static files during development
    if config_name != "production":
        app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    # ── Structured logging ─────────────────────────────────────
    setup_logging(app)

    # ── Initialise extensions ──────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)

    # ── Security: JWT error handlers ───────────────────────────
    register_jwt_handlers(jwt)

    # ── Centralized error handlers ─────────────────────────────
    register_error_handlers(app)

    # ── Register blueprints ────────────────────────────────────
    from auth.routes import auth_bp
    from dashboard.routes import dashboard_bp
    from dashboard.teacher_routes import teacher_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(teacher_bp)

    # ── Context processors ─────────────────────────────────────
    @app.context_processor
    def inject_css_version():
        """Inject a timestamp-based version for cache busting."""
        return {"css_version": int(time.time())}

    # ── Dev-mode cache control ─────────────────────────────────
    if config_name != "production":
        @app.after_request
        def add_header(response):
            if "Cache-Control" not in response.headers:
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
            return response

    # ── Landing page ───────────────────────────────────────────
    @app.route("/")
    def home():
        return render_template("home.html")

    return app


# ── Direct execution ───────────────────────────────────────────
if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        try:
            db.create_all()
            print("=" * 60)
            print("[SUCCESS] Database connected!")
            db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
            if "postgresql" in db_uri:
                print("   Engine: PostgreSQL")
            elif "sqlite" in db_uri:
                print("   Engine: SQLite")
            print("=" * 60)
        except Exception as e:
            print("=" * 60)
            print("[ERROR] Database connection failed!")
            print(f"   Error: {e}")
            print("=" * 60)

    app.run(debug=True)