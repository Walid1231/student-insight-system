"""User identity and authentication tokens."""

from datetime import datetime
from core.extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'teacher'

    # Relationships
    student_profile = db.relationship(
        'StudentProfile', backref='user', uselist=False, cascade="all, delete-orphan"
    )
    teacher_profile = db.relationship(
        'TeacherProfile', backref='user', uselist=False, cascade="all, delete-orphan"
    )
    tokens = db.relationship('UserToken', backref='user', cascade="all, delete-orphan")


class UserToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    access_token = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
