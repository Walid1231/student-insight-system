from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'teacher'
    
    # Relationships
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    teacher_profile = db.relationship('TeacherProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    tokens = db.relationship('UserToken', backref='user', cascade="all, delete-orphan")

class UserToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    access_token = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TeacherAssignment(db.Model):
    """Links teachers to students for specific subjects/classes"""
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher_profile.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    class_level = db.Column(db.String(10))  # e.g., "9", "10"
    section = db.Column(db.String(5))  # e.g., "A", "B"
    subject = db.Column(db.String(100))  # e.g., "Mathematics", "Physics"
    assignment_type = db.Column(db.String(20))  # 'subject' or 'homeroom'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TeacherProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100))
    subject_specialization = db.Column(db.String(100))
    
    # Relationships
    assignments = db.relationship('TeacherAssignment', backref='teacher', cascade="all, delete-orphan")

class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100))
    class_level = db.Column(db.String(10))  # e.g., "9", "10", "11"
    section = db.Column(db.String(5))  # e.g., "A", "B", "C"
    current_cgpa = db.Column(db.Float)
    last_activity = db.Column(db.DateTime)  # Tracks last login/interaction
    
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
    proficiency_score = db.Column(db.Integer, default=0)  # 0-100
    risk_score = db.Column(db.Float, default=0.0)  # 0.0-1.0
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    progress_history = db.relationship('StudentSkillProgress', backref='skill', cascade="all, delete-orphan")

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
    skill_id = db.Column(db.Integer, db.ForeignKey('student_skill.id'), nullable=True) # Optional link to specific skill
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending') # 'pending', 'completed', 'verified'
    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    # Relationships
    student = db.relationship('StudentProfile', backref='action_plans')
    skill = db.relationship('StudentSkill', backref='action_plans')

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


class Attendance(db.Model):
    """Tracks daily attendance for students"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20))  # 'present', 'absent', 'late'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StudentNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher_profile.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_private = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    teacher = db.relationship('TeacherProfile', backref='notes_created')
    student = db.relationship('StudentProfile', backref='notes')

class StudentAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'attendance', 'performance', 'behavior', 'missing_work'
    severity = db.Column(db.String(20), default='info') # 'high', 'medium', 'info'
    message = db.Column(db.String(255), nullable=False)
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('StudentProfile', backref='alerts')

class Assignment(db.Model):
    """Assignments created for students"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(100))
    # Optional link to creator teacher
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher_profile.id')) 
    total_points = db.Column(db.Float)
    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to creator
    teacher = db.relationship('TeacherProfile', backref='assignments_created')

class AssignmentSubmission(db.Model):
    """Student submissions for assignments"""
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    score = db.Column(db.Float)
    submitted_at = db.Column(db.DateTime)
    status = db.Column(db.String(20))  # 'submitted', 'late', 'pending'
    
    # Relationships
    assignment = db.relationship('Assignment', backref='submissions')

class Assessment(db.Model):
    """Quizzes and exams"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20))  # 'quiz', 'exam'
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
    
    # Relationships
    assessment = db.relationship('Assessment', backref='results')

class StudentInsight(db.Model):
    """Stores AI-generated insight reports for students"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    content = db.Column(db.Text, nullable=False) # HTML content of the report
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    student = db.relationship('StudentProfile', backref='insights')
