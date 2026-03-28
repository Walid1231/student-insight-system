"""Student profile and academic metrics."""

import json
from core.extensions import db


class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    student_code = db.Column(db.String(16), unique=True, nullable=True, index=True)
    department = db.Column(db.String(100))
    class_level = db.Column(db.String(10))
    section = db.Column(db.String(5))
    current_cgpa = db.Column(db.Float)
    last_activity = db.Column(db.DateTime)

    # Enhanced tracking
    grading_scale = db.Column(db.Float, default=4.0)
    current_semester = db.Column(db.Integer)
    expected_graduation_date = db.Column(db.Date)
    completed_credits = db.Column(db.Integer)
    target_cgpa = db.Column(db.Float)

    # Relationships
    academic_metrics = db.relationship(
        'AcademicMetric', backref='student', uselist=False, cascade="all, delete-orphan"
    )
    skills = db.relationship('StudentSkill', backref='student', cascade="all, delete-orphan")
    courses = db.relationship('StudentCourse', backref='student', cascade="all, delete-orphan")
    career_interests = db.relationship('CareerInterest', backref='student', cascade="all, delete-orphan")
    analytics_results = db.relationship(
        'AnalyticsResult', backref='student', uselist=False, cascade="all, delete-orphan"
    )
    academic_records = db.relationship('StudentAcademicRecord', backref='student', cascade="all, delete-orphan")
    student_goals = db.relationship('StudentGoal', backref='student', cascade="all, delete-orphan")
    study_sessions = db.relationship('StudySession', backref='student', cascade="all, delete-orphan")
    weekly_updates = db.relationship('WeeklyUpdate', backref='student', cascade="all, delete-orphan")
    chat_history = db.relationship('ChatHistory', backref='student', cascade="all, delete-orphan")
    settings = db.relationship('StudentSettings', backref='student', uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'student_code': self.student_code,
            'full_name': self.full_name,
            'department': self.department,
            'class_level': self.class_level,
            'section': self.section,
            'current_cgpa': self.current_cgpa
        }

    @property
    def performance_status(self):
        """Return performance status: good, average, or at-risk"""
        if not self.current_cgpa:
            return 'unknown'
        if self.current_cgpa >= 3.5:
            return 'good'
        elif self.current_cgpa >= 2.5:
            return 'average'
        else:
            return 'at-risk'


class AcademicMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    semester_gpas = db.Column(db.Text)
    total_credits = db.Column(db.Integer)
    department_rank = db.Column(db.Integer)

    def get_gpas(self):
        return json.loads(self.semester_gpas) if self.semester_gpas else []

    def set_gpas(self, gpas_list):
        self.semester_gpas = json.dumps(gpas_list)


class StudentSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    
    # Email Notifications
    email_weekly_report = db.Column(db.Boolean, default=True)
    email_new_assignments = db.Column(db.Boolean, default=True)
    
    # Appearance
    compact_sidebar = db.Column(db.Boolean, default=False)
    


    def to_dict(self):
        return {
            'email_weekly_report': self.email_weekly_report,
            'email_new_assignments': self.email_new_assignments,
            'compact_sidebar': self.compact_sidebar
        }
