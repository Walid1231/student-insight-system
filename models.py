from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

# -------------------------
# AUTH MODEL (The Missing Piece)
# -------------------------
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'student' or 'teacher'

    # Link User to their Student Profile (One-to-One)
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False)

    def __repr__(self):
        return f'<User {self.email}>'


# -------------------------
# STUDENT DATA MODELS
# -------------------------
class StudentProfile(db.Model):
    __tablename__ = 'student_profile'
    
    id = db.Column(db.Integer, primary_key=True)
    # Link this profile to a specific User account
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(100))
    university = db.Column(db.String(150)) # NEW field
    current_cgpa = db.Column(db.Float)
    
    # Customization Fields
    introduction = db.Column(db.Text) # Bio/Intro
    school = db.Column(db.String(150)) # High School/Previous
    college = db.Column(db.String(150)) # College (if different from Uni)
    profile_picture = db.Column(db.String(255)) # Path to image
    linkedin_link = db.Column(db.String(255))
    facebook_link = db.Column(db.String(255))

    # Relationships
    academic_metrics = db.relationship('AcademicMetric', backref='student', uselist=False, cascade="all, delete-orphan")
    skills = db.relationship('StudentSkill', backref='student', cascade="all, delete-orphan")
    courses = db.relationship('StudentCourse', backref='student', cascade="all, delete-orphan")
    career_interests = db.relationship('CareerInterest', backref='student', cascade="all, delete-orphan")
    analytics_results = db.relationship('AnalyticsResult', backref='student', uselist=False, cascade="all, delete-orphan")
    study_activities = db.relationship('StudyActivity', backref='student', cascade="all, delete-orphan") # NEW Relationship

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'department': self.department,
            'university': self.university,
            'current_cgpa': self.current_cgpa
        }

class AcademicMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    semester_gpas = db.Column(db.Text)  # JSON string of semester GPAs
    total_credits = db.Column(db.Integer)
    department_rank = db.Column(db.Integer)
    target_gpa = db.Column(db.Float) # NEW field
    
    def get_gpas(self):
        return json.loads(self.semester_gpas) if self.semester_gpas else []
        
    def set_gpas(self, gpas_list):
        self.semester_gpas = json.dumps(gpas_list)

class StudyActivity(db.Model): # NEW Model
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    hours = db.Column(db.Float, default=0.0)

class StudentSkill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    proficiency_level = db.Column(db.String(50))  # Beginner, Intermediate, Advanced
    is_target = db.Column(db.Boolean, default=False) # NEW: To distinguish "To Learn" vs "Known"

class StudentCourse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    course_type = db.Column(db.String(20))  # 'strong' or 'weak' or 'average'
    grade = db.Column(db.String(5))
    score = db.Column(db.Integer) # NEW: Store numerical score (0-100) for bar charts

class CareerInterest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    role_name = db.Column(db.String(100), nullable=False) # Renamed from field_name for clarity
    match_score = db.Column(db.Integer)  # 0-100, User input or AI predicted
    
class AnalyticsResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    predicted_next_gpa = db.Column(db.Float)
    career_predictions = db.Column(db.Text)  # JSON string of predicted career fit
    skill_recommendations = db.Column(db.Text)  # JSON list
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_career_predictions(self):
        return json.loads(self.career_predictions) if self.career_predictions else {}

