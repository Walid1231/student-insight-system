"""
Validation schemas for student-related inputs.

Uses Pydantic v2 for fast, declarative validation.
Schemas validate at the HTTP boundary — services receive clean data.
"""

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class StudySessionCreate(BaseModel):
    """Validates study session creation input."""
    date: date
    duration_minutes: int = Field(gt=0, le=1440, description="Max 24 hours")
    topic_studied: str = Field(min_length=1, max_length=200)
    related_skill: Optional[str] = Field(default=None, max_length=100)

    @field_validator("topic_studied")
    @classmethod
    def strip_topic(cls, v):
        return v.strip()

    @classmethod
    def from_form(cls, form):
        """Parse from Flask request.form MultiDict."""
        return cls(
            date=form.get("date"),
            duration_minutes=form.get("duration_minutes"),
            topic_studied=form.get("topic_studied"),
            related_skill=form.get("related_skill") or None,
        )


class StudySessionUpdate(BaseModel):
    """Validates study session update input."""
    topic: Optional[str] = Field(default=None, max_length=200)
    duration: Optional[int] = Field(default=None, gt=0, le=1440)
    skill: Optional[str] = Field(default=None, max_length=100)


class ProfileUpdate(BaseModel):
    """Validates profile edit input."""
    full_name: str = Field(min_length=1, max_length=150)
    university: Optional[str] = Field(default=None, max_length=200)
    department: Optional[str] = Field(default=None, max_length=200)
    current_year: Optional[str] = Field(default=None, max_length=20)
    cgpa: Optional[float] = Field(default=None, ge=0.0, le=4.0)
    career_goal: Optional[str] = Field(default=None, max_length=300)
    linkedin_profile: Optional[str] = Field(default=None, max_length=300)
    github_profile: Optional[str] = Field(default=None, max_length=300)
    bio: Optional[str] = Field(default=None, max_length=1000)


class WeeklyCheckinSubmit(BaseModel):
    """Validates weekly check-in submission."""
    productivity_rating: Optional[int] = Field(default=None, ge=1, le=5)
    mood_score: Optional[int] = Field(default=None, ge=1, le=5)
    difficulty_rating: Optional[str] = Field(default=None)

    @field_validator("difficulty_rating")
    @classmethod
    def validate_difficulty(cls, v):
        if v and v not in ("Easy", "Medium", "Hard"):
            raise ValueError("difficulty_rating must be Easy, Medium, or Hard")
        return v

    @classmethod
    def from_form(cls, form):
        return cls(
            productivity_rating=form.get("productivity_rating") or None,
            mood_score=form.get("mood_score") or None,
            difficulty_rating=form.get("difficulty_rating") or None,
        )
