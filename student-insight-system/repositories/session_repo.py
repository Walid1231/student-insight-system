"""Study session data access."""

from datetime import datetime, timedelta
from sqlalchemy import func
from repositories.base import BaseRepository
from models.sessions import StudySession
from core.extensions import db


class SessionRepository(BaseRepository):
    model = StudySession

    @classmethod
    def get_weekly_hours(cls, student_id, weeks=4):
        """Return total study hours per week for the last N weeks."""
        cutoff = datetime.utcnow().date() - timedelta(weeks=weeks)
        rows = (
            db.session.query(
                func.date_trunc('week', StudySession.date).label('week'),
                func.sum(StudySession.duration_minutes).label('total_mins'),
            )
            .filter(
                StudySession.student_id == student_id,
                StudySession.date >= cutoff,
            )
            .group_by('week')
            .order_by('week')
            .all()
        )
        return [(r.week, round((r.total_mins or 0) / 60, 1)) for r in rows]

    @classmethod
    def get_last_n_days(cls, student_id, days=7):
        """Return all sessions from the last N days."""
        cutoff = datetime.utcnow().date() - timedelta(days=days)
        return (
            cls.model.query
            .filter(
                cls.model.student_id == student_id,
                cls.model.date >= cutoff,
            )
            .order_by(cls.model.date.desc())
            .all()
        )
