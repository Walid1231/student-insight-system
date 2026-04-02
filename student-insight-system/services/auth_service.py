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
        email = (email or "").strip().lower()
        if User.query.filter_by(email=email).first():
            raise ConflictError("An account with this email address already exists. Please login instead.")


        try:
            hashed_password = generate_password_hash(password)
            new_user = User(email=email, password_hash=hashed_password, role=role)
            db.session.add(new_user)
            db.session.flush()

            if role == 'teacher':
                new_teacher = TeacherProfile(user_id=new_user.id, full_name=name, email=email)
                db.session.add(new_teacher)
            elif role == 'student':
                import uuid
                # Generate a guaranteed unique 16-char student_code
                s_code = "STU-" + uuid.uuid4().hex[:12].upper()
                new_student = StudentProfile(
                    user_id=new_user.id, 
                    full_name=name,
                    student_code=s_code
                )
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
        `email` can also be a numeric student_code (students only).

        Returns:
            Dict with 'access_token' and 'role'.
        """
        user = None

        # Try student_code lookup if input is purely numeric
        identifier = (email or "").strip()
        if identifier.isdigit():
            profile = StudentProfile.query.filter_by(
                student_code=identifier
            ).first()
            if profile:
                user = User.query.get(profile.user_id)

        # Fall back to email lookup
        if user is None:
            user = User.query.filter_by(email=identifier).first()

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
