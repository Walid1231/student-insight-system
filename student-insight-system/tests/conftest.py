"""
Shared test fixtures — provides isolated app, client, and DB session.

Usage in tests:
    def test_login(client, auth_headers):
        resp = client.get("/student/dashboard", headers=auth_headers("student"))
        assert resp.status_code == 200
"""

import pytest
from app import create_app
from core.extensions import db as _db
from models import User
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token


@pytest.fixture(scope="session")
def app():
    """Create a test application instance (once per test session)."""
    app = create_app("testing")
    yield app


@pytest.fixture(scope="function")
def db_session(app):
    """Provide a clean database for each test function."""
    with app.app_context():
        _db.create_all()
        yield _db.session
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app, db_session):
    """Flask test client with an active DB session."""
    with app.test_client() as c:
        with app.app_context():
            yield c


@pytest.fixture(scope="function")
def auth_headers(app, db_session):
    """
    Factory fixture that returns auth headers for a given role.

    Usage:
        headers = auth_headers("student")
        headers = auth_headers("teacher")
    """
    def _make(role="student"):
        with app.app_context():
            token = create_access_token(
                identity="999",
                additional_claims={"role": role}
            )
            return {"Authorization": f"Bearer {token}"}
    return _make
