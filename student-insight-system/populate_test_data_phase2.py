"""
Phase 2 Test Data - Student Progress Monitoring
Includes attendance, assignments, assessments for testing
"""
from app import app
from models import (db, User, TeacherProfile, StudentProfile, TeacherAssignment,
                    Attendance, Assignment, AssignmentSubmission, Assessment, AssessmentResult)
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

with app.app_context():
    # Create Teacher
    teacher_user = User(
        email="teacher@test.com",
        password_hash=generate_password_hash("password"),
        role="teacher"
    )
    db.session.add(teacher_user)
    db.session.commit()
    
    teacher_profile = TeacherProfile(
        user_id=teacher_user.id,
        full_name="Dr. Sarah Johnson",
        department="Mathematics",
        subject_specialization="Algebra"
    )
    db.session.add(teacher_profile)
    db.session.commit()
    
    # Create Students
    students_data = [
        {"name": "Alice Smith", "class": "9", "section": "A", "cgpa": 3.8, "dept": "Science"},
        {"name": "Bob Jones", "class": "9", "section": "A", "cgpa": 2.9, "dept": "Science"},
        {"name": "Charlie Brown", "class": "9", "section": "B", "cgpa": 2.2, "dept": "Science"},
        {"name": "Diana Prince", "class": "10", "section": "A", "cgpa": 3.6, "dept": "Science"},
        {"name": "Eve Wilson", "class": "10", "section": "A", "cgpa": 3.1, "dept": "Science"},
        {"name": "Frank Miller", "class": "10", "section": "B", "cgpa": 2.4, "dept": "Science"},
    ]
    
    student_profiles = []
    
    for s_data in students_data:
        # Create user
        user = User(
            email=f"{s_data['name'].lower().replace(' ', '.')}@student.com",
            password_hash=generate_password_hash("password"),
            role="student"
        )
        db.session.add(user)
        db.session.commit()
        
        # Create profile
        student = StudentProfile(
            user_id=user.id,
            full_name=s_data['name'],
            class_level=s_data['class'],
            section=s_data['section'],
            current_cgpa=s_data['cgpa'],
            department=s_data['dept'],
            last_activity=datetime.utcnow() - timedelta(days=random.randint(1, 10))
        )
        db.session.add(student)
        db.session.commit()
        student_profiles.append(student)
        
        # Assign to teacher
        assignment = TeacherAssignment(
            teacher_id=teacher_profile.id,
            student_id=student.id,
            class_level=s_data['class'],
            section=s_data['section'],
            subject="Mathematics",
            assignment_type="subject"
        )
        db.session.add(assignment)
        
        # Generate Attendance (last 30 days)
        for i in range(30):
            date = datetime.utcnow().date() - timedelta(days=i)
            status = random.choices(['present', 'absent', 'late'], weights=[85, 10, 5])[0]
            
            attendance = Attendance(
                student_id=student.id,
                date=date,
                status=status
            )
            db.session.add(attendance)
        
    db.session.commit()
    
    # Create Assignments
    assignments_list = [
        {"title": "Algebra Quiz 1", "subject": "Mathematics", "points": 100, "days_ago": 20},
        {"title": "Geometry Problem Set", "subject": "Mathematics", "points": 50, "days_ago": 15},
        {"title": "Calculus Practice", "subject": "Mathematics", "points": 75, "days_ago": 10},
        {"title": "Statistics Assignment", "subject": "Mathematics", "points": 80, "days_ago": 5},
    ]
    
    for a_data in assignments_list:
        assignment = Assignment(
            title=a_data['title'],
            subject=a_data['subject'],
            total_points=a_data['points'],
            due_date=(datetime.utcnow() - timedelta(days=a_data['days_ago'])).date()
        )
        db.session.add(assignment)
        db.session.commit()
        
        # Create submissions for each student
        for student in student_profiles:
            # Random completion (80% complete assignments)
            if random.random() < 0.8:
                score = random.randint(60, 100) * a_data['points'] / 100
                status = random.choices(['submitted', 'late'], weights=[90, 10])[0]
                
                submission = AssignmentSubmission(
                    assignment_id=assignment.id,
                    student_id=student.id,
                    score=score,
                    submitted_at=datetime.utcnow() - timedelta(days=a_data['days_ago'] - 1),
                    status=status
                )
                db.session.add(submission)
    
    db.session.commit()
    
    # Create Assessments (Quizzes & Exams)
    assessments_list = [
        {"title": "Quiz 1: Linear Equations", "type": "quiz", "points": 100, "days_ago": 25},
        {"title": "Quiz 2: Quadratics", "type": "quiz", "points": 100, "days_ago": 18},
        {"title": "Midterm Exam", "type": "exam", "points": 200, "days_ago": 12},
        {"title": "Quiz 3: Functions", "type": "quiz", "points": 100, "days_ago": 8},
        {"title": "Final Exam", "type": "exam", "points": 200, "days_ago": 3},
    ]
    
    for a_data in assessments_list:
        assessment = Assessment(
            title=a_data['title'],
            type=a_data['type'],
            subject="Mathematics",
            total_points=a_data['points'],
            date=(datetime.utcnow() - timedelta(days=a_data['days_ago'])).date()
        )
        db.session.add(assessment)
        db.session.commit()
        
        # Create results for each student
        for student in student_profiles:
            # Vary scores based on student CGPA (higher CGPA = better scores)
            base_score = 60 + (student.current_cgpa / 4.0) * 30  # 60-90 range
            score = base_score + random.uniform(-10, 10)
            score = max(40, min(100, score))  # Clamp between 40-100
            
            result = AssessmentResult(
                assessment_id=assessment.id,
                student_id=student.id,
                score=score * a_data['points'] / 100,
                percentage=score
            )
            db.session.add(result)
    
    db.session.commit()
    
    print("✅ Phase 2 test data created successfully!")
    print(f"Teacher: teacher@test.com / password")
    print(f"Created {len(students_data)} students")
    print(f"Added 30 days of attendance per student")
    print(f"Created {len(assignments_list)} assignments")
    print(f"Created {len(assessments_list)} assessments")
