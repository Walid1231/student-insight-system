"""
Validation schemas for auth inputs.
"""

from pydantic import BaseModel, Field, field_validator


class RegisterInput(BaseModel):
    """Validates registration input."""
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=6, max_length=200)
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in ("student", "teacher"):
            raise ValueError("Role must be 'student' or 'teacher'")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v.strip().lower()


class LoginInput(BaseModel):
    """Validates login input."""
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=1, max_length=200)
    role: str = Field(default=None)
