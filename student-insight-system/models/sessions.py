"""Study sessions and weekly check-in updates."""

from datetime import datetime
from core.extensions import db


class StudySession(db.Model):
    """
    Granular log of every study session.
    Powers the 'Hours studied for each new skill' chart.
    """
    __tablename__ = 'study_sessions'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)

    date = db.Column(db.Date, default=lambda: datetime.utcnow().date())
    duration_minutes = db.Column(db.Integer, nullable=False)
    topic_studied = db.Column(db.String(255))
    related_skill = db.Column(db.String(255), nullable=True)


class WeeklyUpdate(db.Model):
    """
    The weekly summary submitted by the student.
    Stores the 'Snapshot' of their state for that week.
    """
    __tablename__ = 'weekly_updates'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)

    week_start_date = db.Column(db.Date, nullable=False)

    # Aggregated Metrics
    total_hours_studied = db.Column(db.Float)

    # Self-Reflection
    productivity_rating = db.Column(db.Integer)
    difficulty_rating = db.Column(db.String(20))

    # System Calculated Predictions
    consistency_score = db.Column(db.Float)
    burnout_risk_score = db.Column(db.Float)
    goal_achievability_prob = db.Column(db.Float)
    status_label = db.Column(db.String(50))
    mood_score = db.Column(db.Integer)
    goals_achieved = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
