"""
Auth service — registration, login, token management, password reset.

Extracted from auth/routes.py: register(), login().
"""

import logging
import secrets
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from flask import request as flask_request

from core.errors import NotFoundError, ValidationError, ConflictError, AuthorizationError
from core.extensions import db
from models import User, TeacherProfile, StudentProfile, UserToken, PasswordResetToken

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────
RESET_TOKEN_EXPIRY_MINUTES = 5
RESET_RATE_LIMIT = 3          # max requests per email per hour


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

    # ── Password Reset ─────────────────────────────────────────────

    @staticmethod
    def request_password_reset(email: str) -> bool:
        """
        Generate a reset token and send it via email.
        Returns True always (privacy: never reveal whether email exists).
        """
        from services.email_service import EmailService

        email = (email or "").strip().lower()
        user = User.query.filter_by(email=email).first()

        if not user:
            logger.info("Password reset requested for non-existent email: %s", email)
            return True  # Privacy: don't reveal if email exists

        # Rate limiting — max N requests per email per hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_count = PasswordResetToken.query.filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.created_at >= one_hour_ago,
        ).count()

        if recent_count >= RESET_RATE_LIMIT:
            logger.warning("Rate limit hit for password reset: email=%s", email)
            return True  # Still return True for privacy

        # Invalidate any previous unused tokens
        PasswordResetToken.query.filter_by(
            user_id=user.id, used=False
        ).update({"used": True})

        # Generate new token
        raw_token = secrets.token_hex(32)
        expires = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRY_MINUTES)

        reset_token = PasswordResetToken(
            user_id=user.id,
            token=raw_token,
            expires_at=expires,
        )
        db.session.add(reset_token)
        db.session.commit()

        # Build reset URL
        base_url = flask_request.host_url.rstrip("/")
        reset_url = f"{base_url}/reset-password/{raw_token}"

        # Resolve display name
        user_name = email
        if user.role == "student" and user.student_profile:
            user_name = user.student_profile.full_name or email
        elif user.role == "teacher" and user.teacher_profile:
            user_name = user.teacher_profile.full_name or email

        EmailService.send_reset_email(email, reset_url, user_name)
        logger.info("Password reset token generated for email=%s (expires=%s)", email, expires)
        return True

    @staticmethod
    def validate_reset_token(token: str):
        """
        Check if a reset token is valid.
        Returns the PasswordResetToken object or None.
        """
        reset = PasswordResetToken.query.filter_by(token=token, used=False).first()
        if not reset:
            return None
        if datetime.utcnow() > reset.expires_at:
            return None
        return reset

    @staticmethod
    def reset_password(token: str, new_password: str) -> bool:
        """
        Validate token and update the user's password.
        Returns True on success, raises on failure.
        """
        from services.email_service import EmailService

        reset = AuthService.validate_reset_token(token)
        if not reset:
            raise ValidationError("This reset link is invalid or has expired. Please request a new one.")

        user = User.query.get(reset.user_id)
        if not user:
            raise ValidationError("User account not found.")

        # Update password
        user.password_hash = generate_password_hash(new_password)

        # Mark token as used
        reset.used = True
        db.session.commit()

        # Resolve display name for confirmation email
        user_name = user.email
        if user.role == "student" and user.student_profile:
            user_name = user.student_profile.full_name or user.email
        elif user.role == "teacher" and user.teacher_profile:
            user_name = user.teacher_profile.full_name or user.email

        EmailService.send_password_changed_email(user.email, user_name)
        logger.info("Password reset completed for user_id=%d", user.id)
        return True
