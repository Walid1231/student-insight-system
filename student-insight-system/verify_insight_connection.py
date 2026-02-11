from app import app, db
from models import User, StudentProfile, TeacherProfile, TeacherAssignment, StudentInsight
from datetime import datetime

def verify_connection():
    with app.app_context():
        print("SETTING UP TEST DATA...")
        
        # 1. Create Dummy Student
        student_user = User.query.filter_by(email="test_student_verify@example.com").first()
        if not student_user:
            student_user = User(email="test_student_verify@example.com", password_hash="hash", role="student")
            db.session.add(student_user)
            db.session.commit()
            
        student = StudentProfile.query.filter_by(user_id=student_user.id).first()
        if not student:
            student = StudentProfile(user_id=student_user.id, full_name="Test Student Verify", current_cgpa=3.5)
            db.session.add(student)
            db.session.commit()
        print(f"Student: {student.full_name} (ID: {student.id})")

        # 2. Create Dummy Teacher
        teacher_user = User.query.filter_by(email="test_teacher_verify@example.com").first()
        if not teacher_user:
            teacher_user = User(email="test_teacher_verify@example.com", password_hash="hash", role="teacher")
            db.session.add(teacher_user)
            db.session.commit()
            
        teacher = TeacherProfile.query.filter_by(user_id=teacher_user.id).first()
        if not teacher:
            teacher = TeacherProfile(user_id=teacher_user.id, full_name="Test Teacher Verify")
            db.session.add(teacher)
            db.session.commit()
        print(f"Teacher: {teacher.full_name} (ID: {teacher.id})")

        # 3. Create Insight Report (Simulate Student Action)
        print("\nSIMULATING STUDENT GENERATING REPORT...")
        report_content = "<div><h3>Analysis</h3><p>Test Insight Report Content</p></div>"
        insight = StudentInsight(student_id=student.id, content=report_content, generated_at=datetime.utcnow())
        db.session.add(insight)
        db.session.commit()
        print("Insight Report Saved to DB.")

        # 4. Verify Teacher View (Simulate Teacher Action)
        print("\nVERIFYING TEACHER ACCESS...")
        # The route uses this query:
        retrieved_insight = StudentInsight.query.filter_by(student_id=student.id).order_by(StudentInsight.generated_at.desc()).first()
        
        if retrieved_insight:
            print("SUCCESS: Teacher can retrieve the insight report.")
            print(f"Content Preview: {retrieved_insight.content[:50]}...")
            if retrieved_insight.content == report_content:
                print("Content Match: YES")
            else:
                print("Content Match: NO")
        else:
            print("FAILURE: Teacher cannot retrieve the insight report.")

        # Cleanup
        print("\nCLEANING UP...")
        db.session.delete(insight)
        # Optional: keep users for debugging or delete them
        # db.session.delete(student)
        # db.session.delete(student_user)
        # db.session.delete(teacher)
        # db.session.delete(teacher_user)
        db.session.commit()
        print("Done.")

if __name__ == "__main__":
    verify_connection()
