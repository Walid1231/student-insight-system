from app import create_app
from core.extensions import db
from models.teacher import TeacherAssignment, TeacherProfile
from models.student import StudentProfile

app = create_app()
with app.app_context():
    # Pick the first assignment
    assignment = TeacherAssignment.query.first()
    if assignment:
        print(f"Found assignment ID {assignment.id} for teacher {assignment.teacher_id} student {assignment.student_id}")
        # Try to delete it
        try:
            db.session.delete(assignment)
            db.session.commit()
            print("Successfully deleted assignment!")
        except Exception as e:
            print("ERROR", str(e))
            db.session.rollback()
    else:
        print("No assignments to delete.")
