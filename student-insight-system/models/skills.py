"""Skill tracking, progress history, and AI action plans."""

from datetime import datetime
from core.extensions import db


class Skill(db.Model):
    """
    Master list of skills (e.g., 'Python', 'Communication').
    Used to normalize skill names across the system.
    """
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    skill_name = db.Column(db.String(100), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=True)

    required_for_careers = db.relationship('CareerRequiredSkill', backref='skill', lazy=True)


class StudentSkill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=True)
    skill_name = db.Column(db.String(100), nullable=False) # Fallback/Display name
    proficiency_score = db.Column(db.Integer, default=0)
    risk_score = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    master_skill = db.relationship('Skill', backref='student_records', lazy=True)

    __table_args__ = (
        db.Index('ix_student_skill_student_id', 'student_id'),
    )

    progress_history = db.relationship(
        'StudentSkillProgress', backref='skill', cascade="all, delete-orphan"
    )


class StudentSkillProgress(db.Model):
    """Tracks historical proficiency and risk over time"""
    id = db.Column(db.Integer, primary_key=True)
    student_skill_id = db.Column(db.Integer, db.ForeignKey('student_skill.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    proficiency_score = db.Column(db.Integer)
    risk_score = db.Column(db.Float)


class ActionPlan(db.Model):
    """AI-generated tasks for skill improvement"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('student_skill.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    student = db.relationship('StudentProfile', backref='action_plans')
    skill = db.relationship('StudentSkill', backref='action_plans')
