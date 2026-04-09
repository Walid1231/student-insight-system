"""
Application configuration — environment-aware.

Loads secrets from environment variables (via python-dotenv).
Falls back to sensible dev defaults so the app runs out-of-the-box.

Usage in app factory:
    from config import config_by_name
    app.config.from_object(config_by_name["development"])
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()  # reads .env file if present


class Config:
    """Base configuration — shared across all environments."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-dev-secret-change-me")

    # JWT
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:12345@localhost:5432/student_insight_system"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Gemini AI
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

    # Mail (SMTP) — for password reset emails
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "")
    MAIL_USE_TLS = True


class DevelopmentConfig(Config):
    """Development overrides."""
    DEBUG = True
    SEND_FILE_MAX_AGE_DEFAULT = 0


class TestingConfig(Config):
    """Testing overrides — uses in-memory SQLite."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


class ProductionConfig(Config):
    """Production overrides — secrets MUST come from environment."""
    DEBUG = False
    JWT_COOKIE_SECURE = True
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    def __init__(self):
        # Fail fast if required env vars are missing in production
        required = ["SECRET_KEY", "JWT_SECRET_KEY", "DATABASE_URL"]
        missing = [k for k in required if not os.environ.get(k)]
        if missing:
            raise RuntimeError(
                f"Missing required env vars for production: {', '.join(missing)}"
            )


# Lookup dict used by create_app()
config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
