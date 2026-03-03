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
            .limit(8)
            .all()
        )

        # --- Streak: consecutive weeks with a check-in ---
        all_updates = (
            WeeklyUpdate.query
            .filter(
                WeeklyUpdate.student_id == student.id,
                WeeklyUpdate.week_start_date <= week_start,
            )
            .order_by(WeeklyUpdate.week_start_date.desc())
            .all()
        )
        streak = 0
        expected = week_start
        for u in all_updates:
            if u.week_start_date == expected:
                streak += 1
                expected -= timedelta(days=7)
            else:
                break

        # --- Snapshot: current week's computed metrics ---
        snapshot = None
        if current:
            snapshot = {
                "hours": current.total_hours_studied or 0,
                "consistency": round((current.consistency_score or 0) * 100),
                "burnout": round((current.burnout_risk_score or 0) * 100),
                "goal_prob": round((current.goal_achievability_prob or 0) * 100),
                "status": current.status_label,
            }

        # --- Trend: last 4 weeks of productivity + mood for sparklines ---
        trend_source = list(reversed(history[:4]))
        trend = [
            {"prod": h.productivity_rating, "mood": h.mood_score}
            for h in trend_source
        ]

        return {
            "current_productivity": current.productivity_rating if current else '',
            "current_mood": current.mood_score if current else '',
            "current_difficulty": current.difficulty_rating if current else '',
            "current_goals": current.goals_achieved if current else '',
            "already_submitted": current is not None,
            "snapshot": snapshot,
            "streak": streak,
            "history": history,
            "trend": trend,
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
        if data.goals_achieved is not None:
            update.goals_achieved = data.goals_achieved

        db.session.commit()

        from dashboard.recalculate import recalculate_weekly_update
        recalculate_weekly_update(student.id)

        logger.info("Check-in submitted for student_id=%d", student.id)
