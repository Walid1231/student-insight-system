import sqlite3
import app
from models import db, StudentProfile, AcademicMetric, StudentSkill, StudentCourse, CareerInterest, AnalyticsResult
from werkzeug.security import generate_password_hash
import json

def get_db_connection():
    conn = sqlite3.connect('student_insight.db')
    conn.row_factory = sqlite3.Row
    return conn

def populate():
    # 1. Create Login User (Raw SQLite)
    email = "demo@student.com"
    password = "password123"
    name = "Minuan Ray"
    role = "student"
    hashed_pw = generate_password_hash(password)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    user_id = None
    
    # Check if user exists
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        print(f"User {email} already exists in auth DB.")
        user_id = existing_user['id']
    else:
        print(f"Creating new auth user {email}...")
        cursor.execute(
            'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
            (name, email, hashed_pw, role)
        )
        conn.commit()
        user_id = cursor.lastrowid
        print(f"Created auth user with ID: {user_id}")
    
    conn.close()

    # 2. Populate Student Data (SQLAlchemy)
    with app.app.app_context():
        # Check for profile
        profile = StudentProfile.query.get(user_id)
        
        if not profile:
            print(f"Creating StudentProfile for ID {user_id}...")
            profile = StudentProfile(
                id=user_id, # Manually set ID to match auth user
                full_name=name,
                email=email,
                department="Computer Science",
                current_cgpa=3.75
            )
            db.session.add(profile)
            db.session.commit()
        else:
            print(f"StudentProfile for ID {user_id} already exists.")

        # 3. Add Academic Metrics
        metric = AcademicMetric.query.filter_by(student_id=user_id).first()
        if not metric:
            metric = AcademicMetric(
                student_id=user_id,
                semester_gpas=json.dumps([3.5, 3.6, 3.8, 3.7, 3.9]),
                cumulative_gpa=3.75,
                total_credits=98,
                department_rank=5
            )
            db.session.add(metric)
        
        # 4. Add Skills
        skills_list = ["Python", "Data Analysis", "Machine Learning", "React", "Public Speaking"]
        current_skills = [s.skill_name for s in StudentSkill.query.filter_by(student_id=user_id).all()]
        for s_name in skills_list:
            if s_name not in current_skills:
                db.session.add(StudentSkill(student_id=user_id, skill_name=s_name, proficiency_level="Intermediate"))

        # 5. Add Courses
        courses_data = [
            ("Data Structures", "strong", "A"),
            ("Algorithms", "strong", "A"),
            ("Linear Algebra", "weak", "B-"),
            ("Operating Systems", "strong", "A-")
        ]
        
        # Clear existing courses to avoid duplicates if re-running
        StudentCourse.query.filter_by(student_id=user_id).delete()
        for c_name, c_type, grade in courses_data:
            db.session.add(StudentCourse(student_id=user_id, course_name=c_name, course_type=c_type, grade=grade))

        # 6. Add Analytics Result (Pre-calculated)
        interests = {"Data Science": 85, "Software Engineering": 70, "AI Research": 90}
        
        analytics = AnalyticsResult.query.filter_by(student_id=user_id).first()
        if not analytics:
            analytics = AnalyticsResult(
                student_id=user_id,
                predicted_next_gpa=3.82,
                career_predictions=json.dumps(interests),
                skill_recommendations=json.dumps(["Deep Learning", "TensorFlow", "Statistics"])
            )
            db.session.add(analytics)
        else:
             analytics.career_predictions = json.dumps(interests)
             
        db.session.commit()
        print("Demo data populated successfully!")
        print(f"Login with: {email} / {password}")

if __name__ == "__main__":
    populate()
