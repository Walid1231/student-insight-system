"""
Validation schemas for academic inputs.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class GradeInput(BaseModel):
    """Validates grade/course addition."""
    course_name: str = Field(min_length=1, max_length=150)
    course_type: str = Field(default="Core", max_length=50)
    credit_value: int = Field(default=3, ge=1, le=6)
    semester: int = Field(ge=1, le=20)
    grade: str = Field(min_length=1, max_length=5)

    @field_validator("grade")
    @classmethod
    def validate_grade(cls, v):
        valid = {'A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'D', 'F'}
        if v.upper() not in valid:
            raise ValueError(f"Invalid grade: {v}")
        return v.upper()

    @field_validator("course_name")
    @classmethod
    def strip_course(cls, v):
        return v.strip()

    @classmethod
    def from_form(cls, form):
        return cls(
            course_name=form.get("course_name", ""),
            course_type=form.get("course_type", "Core"),
            credit_value=form.get("credit_value", "3"),
            semester=form.get("semester"),
            grade=form.get("grade"),
        )


class TargetCgpaInput(BaseModel):
    """Validates target CGPA update."""
    target_cgpa: float = Field(ge=0.0, le=4.0)

    @classmethod
    def from_form(cls, form):
        return cls(target_cgpa=form.get("target_cgpa"))


class GoalInput(BaseModel):
    """Validates goal creation."""
    career_id: int = Field(gt=0)
    goal_type: str = Field(default="Long Term", max_length=50)

    @classmethod
    def from_form(cls, form):
        return cls(
            career_id=form.get("career_id"),
            goal_type=form.get("goal_type", "Long Term"),
        )
