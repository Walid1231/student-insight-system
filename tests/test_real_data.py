import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User, StudentProfile, AcademicMetric, StudyActivity
from flask_jwt_extended import create_access_token

def run_tests():
    print("Running real data integration test...")
    app.config['TESTING'] = True
    # Use a separate file DB to ensure isolation and avoid lock issues with the main DB
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_verification.db' 
    app.config['JWT_SECRET_KEY'] = 'test-secret'
    app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for testing forms

    with app.app_context():
        db.create_all()
        test_client = app.test_client()

        # 1. Setup User and Token
        import time
        email = f"realdata_{int(time.time())}@test.com"
        user = User(name="Test User", email=email, password="pw", role="student")
        db.session.add(user)
        db.session.commit()
        
        token = create_access_token(
            identity=email,
            additional_claims={"role": "student", "name": "Test User"}
        )
        headers = {'Authorization': f'Bearer {token}'}
        test_client.set_cookie('access_token_cookie', token)

        # 2. Test Redirect on empty profile
        print("\n[TEST] 1. Redirect on empty profile")
        resp = test_client.get('/student/dashboard/v2', headers=headers)
        if resp.status_code == 302 and 'update-progress' in resp.location:
             print("[PASS] Redirected to update-progress as expected")
        else:
             print(f"[FAIL] Expected redirect, got {resp.status_code}")

        # 3. Submit Data via update_progress
        print("\n[TEST] 2. Submitting Profile Data")
        form_data = {
            "university": "Test Uni",
            "department": "CS",
            "current_cgpa": "3.5",
            "target_gpa": "3.9",
            "subject_1": "Math", "score_1": "90",
            "role_1": "Dev", "match_1": "95",
            "skills_known": "Python, SQL",
            "skills_todo": "Rust",
            "h_mon": "5", "h_tue": "4"
        }
        resp = test_client.post('/update-progress', data=form_data, headers=headers)
        
        if resp.status_code == 302 and 'student/dashboard/v2' in resp.location:
            print("[PASS] Data submitted, redirected to dashboard")
        else:
             print(f"[FAIL] Submission failed: {resp.status_code}")

        # 4. Verify Dashboard Rendering with Data
        print("\n[TEST] 3. Verifying Dashboard Content")
        resp = test_client.get('/student/dashboard/v2', headers=headers)
        content = resp.get_data(as_text=True)
        
        checks = [
            "Test Uni", "3.5", "3.9", "Math", "Dev", "Python", "Rust"
        ]
        
        failed_checks = [c for c in checks if c not in content]
        
        if not failed_checks:
            print("[PASS] All data points visible on dashboard")
        else:
             print(f"[FAIL] Missing data: {failed_checks}")

    # Cleanup
    try:
        if os.path.exists("test_verification.db"):
            os.remove("test_verification.db")
            print("[INFO] Cleaned up test database.")
    except Exception as e:
        print(f"[WARN] Could not clean up test database: {e}")

if __name__ == "__main__":
    run_tests()
