"""Assignments, quizzes, exams, and student submissions."""

from datetime import datetime
from core.extensions import db


class Assignment(db.Model):
    """Assignments created for students"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(100))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher_profile.id'))
    total_points = db.Column(db.Float)
    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship('TeacherProfile', backref='assignments_created')


class AssignmentSubmission(db.Model):
    """Student submissions for assignments"""
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    score = db.Column(db.Float)
    submitted_at = db.Column(db.DateTime)
    status = db.Column(db.String(20))

    assignment = db.relationship('Assignment', backref='submissions')


class Assessment(db.Model):
    """Quizzes and exams"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20))
    subject = db.Column(db.String(100))
    total_points = db.Column(db.Float)
    date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AssessmentResult(db.Model):
    """Student results for quizzes/exams"""
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessment.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    score = db.Column(db.Float)
    percentage = db.Column(db.Float)

    assessment = db.relationship('Assessment', backref='results')
