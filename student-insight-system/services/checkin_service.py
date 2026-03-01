"""
Weekly check-in service.

Extracted from routes.py: weekly_checkin(), submit_weekly_checkin().
"""

import logging
from datetime import datetime, timedelta

from core.errors import NotFoundError
from core.extensions import db
from models import StudentProfile, WeeklyUpdate

logger = logging.getLogger(__name__)


class CheckinService:
    """Weekly check-in business logic — HTTP-unaware."""

    @staticmethod
    def _get_student(user_id):
        student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
        if not student:
            raise NotFoundError("Student not found")
        return student

    @staticmethod
    def get_checkin_data(user_id: str) -> dict:
        """Build data for the weekly check-in page."""
        student = CheckinService._get_student(user_id)

        today = datetime.utcnow().date()
        week_start = today - timedelta(days=today.weekday())

        current = WeeklyUpdate.query.filter_by(
            student_id=student.id, week_start_date=week_start
        ).first()

        history = (
            WeeklyUpdate.query
            .filter(
                WeeklyUpdate.student_id == student.id,
                WeeklyUpdate.week_start_date < week_start,
            )
            .order_by(WeeklyUpdate.week_start_date.desc())
            .limit(4)
            .all()
        )

        return {
            "current_productivity": current.productivity_rating if current else '',
            "current_mood": current.mood_score if current else '',
            "current_difficulty": current.difficulty_rating if current else '',
            "current_goals": current.status_label if current else '',
            "history": history,
        }

    @staticmethod
    def submit_checkin(user_id: str, data) -> None:
        """Save check-in data and trigger recalculation."""
        student = CheckinService._get_student(user_id)

        today = datetime.utcnow().date()
        week_start = today - timedelta(days=today.weekday())

        update = WeeklyUpdate.query.filter_by(
            student_id=student.id, week_start_date=week_start
        ).first()

        if not update:
            update = WeeklyUpdate(student_id=student.id, week_start_date=week_start)
            db.session.add(update)

        if data.productivity_rating is not None:
            update.productivity_rating = data.productivity_rating
        if data.mood_score is not None:
            update.mood_score = data.mood_score
        if data.difficulty_rating is not None:
            update.difficulty_rating = data.difficulty_rating

        db.session.commit()

        from dashboard.recalculate import recalculate_weekly_update
        recalculate_weekly_update(student.id)

        logger.info("Check-in submitted for student_id=%d", student.id)
