from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(100))
    current_cgpa = db.Column(db.Float)
    
    # Relationships
    academic_metrics = db.relationship('AcademicMetric', backref='student', uselist=False, cascade="all, delete-orphan")
    skills = db.relationship('StudentSkill', backref='student', cascade="all, delete-orphan")
    courses = db.relationship('StudentCourse', backref='student', cascade="all, delete-orphan")
    career_interests = db.relationship('CareerInterest', backref='student', cascade="all, delete-orphan")
    analytics_results = db.relationship('AnalyticsResult', backref='student', uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'department': self.department,
            'current_cgpa': self.current_cgpa
        }

class AcademicMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    semester_gpas = db.Column(db.Text)  # JSON string of semester GPAs
    total_credits = db.Column(db.Integer)
    department_rank = db.Column(db.Integer)
    
    def get_gpas(self):
        return json.loads(self.semester_gpas) if self.semester_gpas else []
        
    def set_gpas(self, gpas_list):
        self.semester_gpas = json.dumps(gpas_list)

class StudentSkill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    proficiency_level = db.Column(db.String(50))  # Beginner, Intermediate, Advanced

class StudentCourse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    course_type = db.Column(db.String(20))  # 'strong' or 'weak'
    grade = db.Column(db.String(5))

class CareerInterest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    field_name = db.Column(db.String(100), nullable=False)
    interest_score = db.Column(db.Float)  # 0-100, AI predicted
    
class AnalyticsResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    predicted_next_gpa = db.Column(db.Float)
    career_predictions = db.Column(db.Text)  # JSON string of predicted career fit
    skill_recommendations = db.Column(db.Text)  # JSON list
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_career_predictions(self):
        return json.loads(self.career_predictions) if self.career_predictions else {}

