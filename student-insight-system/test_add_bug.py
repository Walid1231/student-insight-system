import traceback
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User
from services.academic_service import AcademicService

def test_add_goal():
    app = create_app()
    with app.app_context():
        # Find a real student ID
        student_user = User.query.filter_by(role="student").first()
        if not student_user:
            print("No student use found")
            return
        
        print(f"Testing for user ID {student_user.id}")
        
        # We need a career ID
        try:
            # Let's use career ID 1, assuming it exists
            goal_id = AcademicService.add_goal(str(student_user.id), 1, "Long Term")
            print(f"Success! Goal ID: {goal_id}")
        except Exception as e:
            print("Exception occurred!")
            traceback.print_exc()

if __name__ == "__main__":
    test_add_goal()
