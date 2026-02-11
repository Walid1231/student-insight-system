"""
Teacher Dashboard Test Data Population
Based on Refined Requirements.
"""
from app import app
from models import (db, User, TeacherProfile, StudentProfile, TeacherAssignment,
                    Attendance, Assignment, AssignmentSubmission, Assessment, AssessmentResult,
                    StudentNote, StudentAlert, AcademicMetric, StudentSkill, CareerInterest, AnalyticsResult)
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

with app.app_context():
    # RESET DB
    print("🗑️  Dropping all tables...")
    db.drop_all()
    print("✨ Creating all tables...")
    db.create_all()

    # --- TEACHERS ---
    print("👨‍🏫 Creating Teachers...")
    t1_user = User(email="teacher@test.com", password_hash=generate_password_hash("password"), role="teacher")
    db.session.add(t1_user)
    db.session.commit()

    teacher1 = TeacherProfile(
        user_id=t1_user.id,
        full_name="Dr. Sarah Johnson",
        department="Mathematics",
        subject_specialization="Algebra & Calculus"
    )
    db.session.add(teacher1)
    db.session.commit()

    # --- STUDENTS ---
    print("🎓 Creating Students...")
    students_data = [
        # Class 10-A (Math)
        {"name": "Alice Smith", "class": "10", "section": "A", "cgpa": 3.8, "status": "good"},
        {"name": "Bob Jones", "class": "10", "section": "A", "cgpa": 2.9, "status": "average"},
        {"name": "Charlie Brown", "class": "10", "section": "A", "cgpa": 2.1, "status": "at-risk"},
        
        # Class 10-B (Math)
        {"name": "Diana Prince", "class": "10", "section": "B", "cgpa": 3.9, "status": "good"},
        {"name": "Eve Wilson", "class": "10", "section": "B", "cgpa": 1.8, "status": "at-risk"},
        
        # Class 9-A (Math)
        {"name": "Frank Miller", "class": "9", "section": "A", "cgpa": 3.2, "status": "average"},
        {"name": "Grace Hopper", "class": "9", "section": "A", "cgpa": 4.0, "status": "good"},
    ]

    student_objs = []

    for s_data in students_data:
        u = User(
            email=f"{s_data['name'].lower().replace(' ', '.')}@student.com",
            password_hash=generate_password_hash("password"),
            role="student"
        )
        db.session.add(u)
        db.session.commit()

        # Create Profile
        p = StudentProfile(
            user_id=u.id,
            full_name=s_data['name'],
            class_level=s_data['class'],
            section=s_data['section'],
            current_cgpa=s_data['cgpa'],
            department="General",
            last_activity=datetime.utcnow() - timedelta(hours=random.randint(1, 48))
        )
        db.session.add(p)
        db.session.commit()
        student_objs.append(p)

        # Assign to Teacher 1 (Math)
        assign = TeacherAssignment(
            teacher_id=teacher1.id,
            student_id=p.id,
            class_level=s_data['class'],
            section=s_data['section'],
            subject="Mathematics",
            assignment_type="subject"
        )
        db.session.add(assign)

        # Create Academic Metrics (needed for dashboard chart)
        # Fix: Ensure JSON string for semester_gpas
        gpas_list = [3.0, 3.2, 3.1, 3.4, 3.8] # dummy trend
        if s_data['status'] == 'at-risk': gpas_list = [3.0, 2.8, 2.5, 2.2, 2.1]
        
        import json
        metric = AcademicMetric(
            student_id=p.id,
            total_credits=45,
            department_rank=random.randint(1, 100),
            semester_gpas=json.dumps(gpas_list)
        )
        db.session.add(metric)
        
        # Skills & Career (dummy)
        skill = StudentSkill(student_id=p.id, skill_name="Python", proficiency_level="Intermediate")
        db.session.add(skill)
        interest = CareerInterest(student_id=p.id, field_name="Data Science", interest_score=85.0)
        db.session.add(interest)

        # Analytics Result (dummy)
        analytics = AnalyticsResult(
             student_id=p.id,
             predicted_next_gpa=s_data['cgpa'], # simple placeholder
             career_predictions='{"Data Scientist": 85, "Software Engineer": 75}',
             skill_recommendations='["SQL", "Machine Learning"]'
        )
        db.session.add(analytics)

    db.session.commit()

    # --- ATTENDANCE ---
    print("📅 Generating Attendance...")
    for s_obj in student_objs:
        # Generate last 30 days
        for i in range(30):
            date = datetime.utcnow().date() - timedelta(days=i)
            # Default good attendance
            weights = [90, 5, 5]
            if s_obj.current_cgpa < 2.5: weights = [60, 30, 10] # Struggling student has worse attendance
            
            status = random.choices(['present', 'absent', 'late'], weights=weights)[0]
            db.session.add(Attendance(student_id=s_obj.id, date=date, status=status))
    db.session.commit()

    # --- ASSIGNMENTS ---
    print("📝 Creating Assignments...")
    # Teacher 1 creates assignments
    assignments_list = [
        {"title": "Algebra Quiz 1", "points": 20, "days_ago": 15},
        {"title": "Mid-term Project", "points": 100, "days_ago": 10},
        {"title": "Trigonometry Worksheet", "points": 50, "days_ago": 5},
    ]

    assignment_objs = []
    for a_data in assignments_list:
        obj = Assignment(
            title=a_data['title'],
            subject="Mathematics",
            teacher_id=teacher1.id, # LINKED TO TEACHER
            total_points=a_data['points'],
            due_date=(datetime.utcnow() - timedelta(days=a_data['days_ago']-2)).date(),
            created_at=datetime.utcnow() - timedelta(days=a_data['days_ago'])
        )
        db.session.add(obj)
        db.session.commit()
        assignment_objs.append(obj)

    # Submissions (Note: Iterate over student_objs directly)
    for s_obj in student_objs:
        for a_obj in assignment_objs:
            # Random score based on capability
            c = s_obj.current_cgpa
            if c is None: c = 2.0 # Fallback
            
            perf_factor = c / 4.0 # 0.5 to 1.0
            score = a_obj.total_points * perf_factor * random.uniform(0.8, 1.0)
            status = 'submitted'
            if random.random() < 0.1: status = 'late'
            if c < 2.5 and random.random() < 0.3: continue # At-risk students miss assignments

            sub = AssignmentSubmission(
                assignment_id=a_obj.id,
                student_id=s_obj.id,
                score=int(score) if score else 0,
                submitted_at=datetime.utcnow(),
                status=status
            )
            db.session.add(sub)
    db.session.commit()

    # --- NOTES & ALERTS ---
    print("🔔 Creating Notes & Alerts...")
    
    # Add notes for at-risk students
    # Filter by checking CGPA directly from object
    at_risk_students = [s for s in student_objs if s.current_cgpa and s.current_cgpa < 2.5]
    for s in at_risk_students:
        db.session.add(StudentNote(
            student_id=s.id,
            teacher_id=teacher1.id,
            content=f"Student {s.full_name} is struggling with Algebra concepts. Need to schedule extra help.",
            is_private=True
        ))
        
        db.session.add(StudentAlert(
            student_id=s.id,
            type="performance",
            severity="high",
            message=f"CGPA dropped below 2.5 threshold.",
            is_resolved=False
        ))
        
        # Attendance alert for one of them
        if random.random() > 0.5:
            db.session.add(StudentAlert(
                student_id=s.id,
                type="attendance",
                severity="medium",
                message="Absent for 3 consecutive days.",
                is_resolved=False
            ))

    # Add note for a good student
    good_students = [s for s in student_objs if s.current_cgpa and s.current_cgpa > 3.5]
    if good_students:
        good_student = good_students[0]
        db.session.add(StudentNote(
            student_id=good_student.id,
            teacher_id=teacher1.id,
            content="Excellent performance in mid-term. Recommended for advanced track.",
            is_private=True
        ))

    db.session.commit()
    print("✅ Teacher Dashboard Data Populated Successfully!")
    print("Login: teacher@test.com / password")
