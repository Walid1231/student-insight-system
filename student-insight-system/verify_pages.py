from app import app
from flask_jwt_extended import create_access_token
from models import User, StudentProfile, db

def verify_new_pages():
    with app.app_context():
        print("VERIFYING NEW ROUTES...")
        
        # 1. Setup Test User
        user = User.query.filter_by(email="test_student_verify@example.com").first()
        if not user:
            print("Creating test user...")
            user = User(email="test_student_verify@example.com", password_hash="hash", role="student")
            db.session.add(user)
            db.session.commit()
            
        student = StudentProfile.query.filter_by(user_id=user.id).first()
        if not student:
             student = StudentProfile(user_id=user.id, full_name="Test Student Verify", current_cgpa=3.5)
             db.session.add(student)
             db.session.commit()

        # 2. Get Token & Set Cookie
        access_token = create_access_token(identity=str(user.id), additional_claims={"role": "student"})
        
        client = app.test_client()
        client.set_cookie('access_token_cookie', access_token)
        
        # 3. Test Profile Page
        print("\nTesting /student/profile...")
        res = client.get("/student/profile")
        if res.status_code == 200:
            print("SUCCESS: Profile page loaded.")
            if b"My Profile" in res.data or b"Edit Profile" in res.data:
                print("Content Check: PASSED")
            else:
                print("Content Check: FAILED (Title not found)")
        else:
            print(f"FAILURE: Profile page status {res.status_code}")
            
        # 4. Test Routine Page
        print("\nTesting /student/routine...")
        res = client.get("/student/routine")
        if res.status_code == 200:
            print("SUCCESS: Routine page loaded.")
            if b"Weekly Routine" in res.data:
                print("Content Check: PASSED")
            else:
                print("Content Check: FAILED")
        else:
             print(f"FAILURE: Routine page status {res.status_code}")

        # 5. Test Update Data Page
        print("\nTesting /student/update-data...")
        res = client.get("/student/update-data")
        if res.status_code == 200:
            print("SUCCESS: Update Data page loaded.")
            if b"Update Dashboard Data" in res.data:
                print("Content Check: PASSED")
            else:
                print("Content Check: FAILED")
        else:
             print(f"FAILURE: Update Data page status {res.status_code}")

if __name__ == "__main__":
    verify_new_pages()
