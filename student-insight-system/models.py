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
    
    # New fields for enhanced tracking
    grading_scale = db.Column(db.Float, default=4.0)
    current_semester = db.Column(db.Integer)
    expected_graduation_date = db.Column(db.Date)
    completed_credits = db.Column(db.Integer)
    
    # Relationships
    academic_metrics = db.relationship('AcademicMetric', backref='student', uselist=False, cascade="all, delete-orphan")
    skills = db.relationship('StudentSkill', backref='student', cascade="all, delete-orphan")
    courses = db.relationship('StudentCourse', backref='student', cascade="all, delete-orphan")
    career_interests = db.relationship('CareerInterest', backref='student', cascade="all, delete-orphan")
    analytics_results = db.relationship('AnalyticsResult', backref='student', uselist=False, cascade="all, delete-orphan")
    
    # New relationships for granular tracking
    academic_records = db.relationship('StudentAcademicRecord', backref='student', cascade="all, delete-orphan")
    student_goals = db.relationship('StudentGoal', backref='student', cascade="all, delete-orphan")
    study_sessions = db.relationship('StudySession', backref='student', cascade="all, delete-orphan")
    weekly_updates = db.relationship('WeeklyUpdate', backref='student', cascade="all, delete-orphan")
    chat_history = db.relationship('ChatHistory', backref='student', cascade="all, delete-orphan")

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


# -------------------------
# MASTER DATA (The System's Knowledge)
# -------------------------

class CourseCatalog(db.Model):
    """
    The official list of courses. 
    Crucial for the 'Strength/Weakness Map' (Core vs GED).
    """
    __tablename__ = 'course_catalog'
    
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(150), nullable=False)
    department = db.Column(db.String(100))
    course_type = db.Column(db.String(50))  # 'Core', 'GED', 'Elective'
    credit_value = db.Column(db.Integer, default=3)
    
    # Relationship to see who took this course
    student_records = db.relationship('StudentAcademicRecord', backref='catalog_course', lazy=True)

class Skill(db.Model):
    """
    Master list of skills (e.g., 'Python', 'Communication').
    Used to normalize skill names across the system.
    """
    __tablename__ = 'skills'
    
    id = db.Column(db.Integer, primary_key=True)
    skill_name = db.Column(db.String(100), unique=True, nullable=False)
    
    # Relationships
    required_for_careers = db.relationship('CareerRequiredSkill', backref='skill', lazy=True)

class CareerPath(db.Model):
    """
    Standard definitions of careers.
    Used for the 'Career Compatibility' logic.
    """
    __tablename__ = 'career_paths'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)  # e.g., 'Software Engineer'
    field_category = db.Column(db.String(100))         # e.g., 'IT', 'Data Science'
    description = db.Column(db.Text)
    
    # Relationship: What skills does this career need?
    required_skills = db.relationship('CareerRequiredSkill', backref='career', lazy=True)

class CareerRequiredSkill(db.Model):
    """
    The link between a Career and a Skill.
    Example: 'Software Engineer' (ID 1) requires 'Python' (ID 5) with 'High' importance.
    """
    __tablename__ = 'career_required_skills'
    
    id = db.Column(db.Integer, primary_key=True)
    career_id = db.Column(db.Integer, db.ForeignKey('career_paths.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    importance_level = db.Column(db.String(20))  # 'High', 'Medium', 'Low'

# -------------------------
# ROUTINE & EFFORT TRACKING (The Truth Mirror)
# -------------------------

class StudySession(db.Model):
    """
    Granular log of every study session.
    Replaces your simple 'StudyActivity'. 
    Powers the 'Hours studied for each new skill' chart.
    """
    __tablename__ = 'study_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    
    date = db.Column(db.Date, default=datetime.utcnow)
    duration_minutes = db.Column(db.Integer, nullable=False)  # Store in minutes for precision
    topic_studied = db.Column(db.String(255))                 # Specific topic text
    
    # Link to a specific skill by name (no longer using foreign key)
    related_skill = db.Column(db.String(255), nullable=True)

class WeeklyUpdate(db.Model):
    """
    The weekly summary submitted by the student.
    Stores the 'Snapshot' of their state for that week.
    """
    __tablename__ = 'weekly_updates'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    
    week_start_date = db.Column(db.Date, nullable=False)
    
    # Aggregated Metrics
    total_hours_studied = db.Column(db.Float)
    
    # Self-Reflection (The "Truth Mirror" Inputs)
    productivity_rating = db.Column(db.Integer)  # 1-5
    difficulty_rating = db.Column(db.String(20))  # 'Easy', 'Medium', 'Hard'
    
    # System Calculated Predictions (Snapshot for history)
    consistency_score = db.Column(db.Float)
    burnout_risk_score = db.Column(db.Float)
    goal_achievability_prob = db.Column(db.Float)
    status_label = db.Column(db.String(50))  # 'On Track', 'At Risk', etc.
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# -------------------------
# UPDATED STUDENT RECORDS
# -------------------------

class StudentAcademicRecord(db.Model):
    """
    Replacement for 'StudentCourse'. 
    Links to 'CourseCatalog' to know if it's Core/GED automatically.
    """
    __tablename__ = 'student_academic_records'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course_catalog.id'), nullable=False)
    
    grade = db.Column(db.String(5))    # 'A-', 'B'
    grade_point = db.Column(db.Float)  # 4.0, 3.7 (Calculated)
    
    # Crucial for "Self-confidence in subject" input
    confidence_score = db.Column(db.Integer)  # 1-5
    semester_taken = db.Column(db.Integer)    # e.g., 3

class StudentGoal(db.Model):
    """
    Replacement for 'CareerInterest'.
    Links specific CareerPaths to the student with context.
    """
    __tablename__ = 'student_goals'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    career_id = db.Column(db.Integer, db.ForeignKey('career_paths.id'), nullable=False)
    
    goal_type = db.Column(db.String(50))  # 'Short Term', 'Long Term'
    reason = db.Column(db.String(50))     # 'Interest', 'Financial', 'Growth'
    is_primary = db.Column(db.Boolean, default=False)

# -------------------------
# CHAT / RAG MODEL
# -------------------------

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
    
    # Stores the JSON snapshot of stats used to generate the answer
    context_data_snapshot = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
