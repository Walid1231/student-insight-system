"""Student alerts, teacher notes, and attendance."""

from datetime import datetime
from core.extensions import db


class Attendance(db.Model):
    """Tracks daily attendance for students"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class StudentNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher_profile.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_private = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    teacher = db.relationship('TeacherProfile', backref='notes_created')
    student = db.relationship('StudentProfile', backref='notes')


class StudentAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), default='info')
    message = db.Column(db.String(255), nullable=False)
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index('ix_student_alert_student_resolved', 'student_id', 'is_resolved'),
        db.Index('ix_student_alert_created_at', 'created_at'),
    )

    student = db.relationship('StudentProfile', backref='alerts')
