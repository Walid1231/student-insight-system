"""Teacher profile and teacher-student assignments."""

from datetime import datetime
from core.extensions import db


class TeacherProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100))
    subject_specialization = db.Column(db.String(100))

    # Relationships
    assignments = db.relationship(
        'TeacherAssignment', backref='teacher', cascade="all, delete-orphan"
    )


class TeacherAssignment(db.Model):
    """Links teachers to students for specific subjects/classes"""
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher_profile.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    class_level = db.Column(db.String(10))
    section = db.Column(db.String(5))
    subject = db.Column(db.String(100))
    assignment_type = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('teacher_id', 'student_id', name='uq_teacher_student_assignment'),
        db.Index('ix_teacher_assignment_teacher_id', 'teacher_id'),
        db.Index('ix_teacher_assignment_student_id', 'student_id'),
    )
