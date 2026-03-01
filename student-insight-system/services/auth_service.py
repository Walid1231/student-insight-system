"""
Auth service — registration, login, token management.

Extracted from auth/routes.py: register(), login().
"""

import logging

from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token

from core.errors import NotFoundError, ValidationError, ConflictError, AuthorizationError
from core.extensions import db
from models import User, TeacherProfile, StudentProfile, UserToken

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication business logic — HTTP-unaware."""

    @staticmethod
    def register_user(name: str, email: str, password: str, role: str) -> dict:
        """Register a new user with profile. Returns success dict."""
        if User.query.filter_by(email=email).first():
            raise ConflictError("User already exists")

        try:
            hashed_password = generate_password_hash(password)
            new_user = User(email=email, password_hash=hashed_password, role=role)
            db.session.add(new_user)
            db.session.commit()

            if role == 'teacher':
                new_teacher = TeacherProfile(user_id=new_user.id, full_name=name)
                db.session.add(new_teacher)
            elif role == 'student':
                new_student = StudentProfile(user_id=new_user.id, full_name=name)
                db.session.add(new_student)

            db.session.commit()
            logger.info("User registered: email=%s, role=%s", email, role)
            return {"msg": "Registration successful", "email": email}

        except Exception as e:
            db.session.rollback()
            logger.exception("Registration failed for email=%s", email)
            raise ValidationError(f"Registration error: {str(e)}")

    @staticmethod
    def login_user(email: str, password: str, requested_role: str = None) -> dict:
        """
        Authenticate user and create JWT token.

        Returns:
            Dict with 'access_token' and 'role'.
        """
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            raise AuthorizationError("Invalid credentials")

        if requested_role and user.role != requested_role:
            raise AuthorizationError(
                f"Access denied. You are registered as a {user.role}, "
                f"please login with the correct role."
            )

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"role": user.role},
        )

        new_token = UserToken(user_id=user.id, access_token=access_token)
        db.session.add(new_token)
        db.session.commit()

        logger.info("User logged in: email=%s, role=%s", email, user.role)
        return {"access_token": access_token, "role": user.role}
