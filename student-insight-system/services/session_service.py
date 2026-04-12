"""
Study session service — CRUD + routine data aggregation.

Extracted from routes.py: student_routine(), add_study_session(), update_study_session().
"""

import logging
from datetime import datetime, timedelta
from collections import defaultdict

from core.errors import NotFoundError
from core.extensions import db
from models import StudentProfile, StudySession, Skill

logger = logging.getLogger(__name__)


class SessionService:
    """Study session business logic — HTTP-unaware."""

    @staticmethod
    def _get_student(user_id):
        student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
        if not student:
            raise NotFoundError("Student profile not found")
        return student

    @staticmethod
    def get_routine_data(user_id: str) -> dict:
        """Build data for the weekly routine calendar view."""
        student = SessionService._get_student(user_id)

        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        all_sessions = StudySession.query.filter_by(
            student_id=student.id
        ).order_by(StudySession.date.desc()).all()

        sessions_by_date = defaultdict(list)
        for s in all_sessions:
            date_key = s.date.strftime('%Y-%m-%d')
            sessions_by_date[date_key].append({
                'id': s.id,
                'topic': s.topic_studied,
                'duration': s.duration_minutes,
                'skill': s.related_skill or '',
            })

        weekly_sessions = StudySession.query.filter(
            StudySession.student_id == student.id,
            StudySession.date >= week_start,
            StudySession.date <= week_end,
        ).all()

        total_hours = sum(s.duration_minutes for s in weekly_sessions) / 60.0

        topic_counts = {}
        for session in weekly_sessions:
            topic = session.topic_studied
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        top_topic = max(topic_counts.items(), key=lambda x: x[1]) if topic_counts else None

        logger.info("Routine data loaded for student_id=%d", student.id)

        return {
            "sessions": all_sessions,
            "sessions_by_date": dict(sessions_by_date),
            "total_hours": round(total_hours, 1),
            "session_count": len(weekly_sessions),
            "top_topic": top_topic[0] if top_topic else None,
            "top_topic_count": top_topic[1] if top_topic else 0,
            "current_year": today.year,
            "current_month": today.month,
            "all_skills": Skill.query.order_by(Skill.skill_name).all(),
        }

    @staticmethod
    def create_session(user_id: str, data) -> StudySession:
        """Create a study session and trigger recalculation."""
        student = SessionService._get_student(user_id)

        session = StudySession(
            student_id=student.id,
            date=data.date,
            duration_minutes=data.duration_minutes,
            topic_studied=data.topic_studied,
            related_skill=data.related_skill if data.related_skill else None,
        )
        db.session.add(session)
        db.session.commit()

        # Recalculate dashboard data
        from dashboard.recalculate import recalculate_weekly_update
        recalculate_weekly_update(student.id)

        logger.info("Study session created for student_id=%d, topic=%s",
                     student.id, data.topic_studied)
        return session

    @staticmethod
    def update_session(user_id: str, session_id: int, data) -> dict:
        """Update an existing study session. Returns serialised session."""
        student = SessionService._get_student(user_id)

        session = StudySession.query.get(session_id)
        if not session or session.student_id != student.id:
            raise NotFoundError("Session not found")

        if data.get("topic"):
            session.topic_studied = data["topic"]
        if data.get("duration"):
            try:
                session.duration_minutes = int(data["duration"])
            except (ValueError, TypeError):
                pass
        if "skill" in data:
            session.related_skill = data["skill"] if data["skill"] else None

        db.session.commit()

        logger.info("Study session %d updated", session_id)
        return {
            "id": session.id,
            "topic": session.topic_studied,
            "duration": session.duration_minutes,
            "skill": session.related_skill or "",
        }

    @staticmethod
    def delete_session(user_id: str, session_id: int) -> None:
        """Delete a study session. Raises NotFoundError if not found or wrong owner."""
        student = SessionService._get_student(user_id)

        session = StudySession.query.get(session_id)
        if not session or session.student_id != student.id:
            raise NotFoundError("Session not found")

        db.session.delete(session)
        db.session.commit()
        logger.info("Study session %d deleted by student_id=%d", session_id, student.id)
