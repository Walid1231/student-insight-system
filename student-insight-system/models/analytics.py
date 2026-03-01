"""Analytics results, AI insights, and chat history."""

import json
from datetime import datetime
from core.extensions import db


class AnalyticsResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    predicted_next_gpa = db.Column(db.Float)
    career_predictions = db.Column(db.Text)
    skill_recommendations = db.Column(db.Text)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    def get_career_predictions(self):
        return json.loads(self.career_predictions) if self.career_predictions else {}


class StudentInsight(db.Model):
    """Stores AI-generated insight reports for students"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('StudentProfile', backref='insights')


class ChatHistory(db.Model):
    """
    For the "Chat with System" feature.
    Stores user questions and system-generated answers.
    """
    __tablename__ = 'chat_history'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)

    user_question = db.Column(db.Text, nullable=False)
    system_answer = db.Column(db.Text, nullable=False)

    context_data_snapshot = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
