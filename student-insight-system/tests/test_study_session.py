
import sys
import os
import random
import string
from datetime import datetime

# Add parent directory to path to import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User, StudentProfile, StudySession

def generate_random_string(length=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def run_verification():
    print("="*60)
    print("VERIFYING STUDY SESSION TRACKING")
    print("="*60)

    # 1. Setup Test Data
    test_email = f"test_student_{generate_random_string()}@example.com"
    test_password = "password123"
    test_name = "Study Test Student"

    print(f"[SETUP] Creating test user: {test_email}")

    with app.app_context():
        # Create User & Profile
        user = User(email=test_email, password_hash="dummy_hash", role="student")
        # In real app hash is needed for login, but we can perhaps mock login or just use helper
        # Wait, the auth flow uses check_password_hash. I need a real hash or use the registration endpoint.
        # Let's use the registration endpoint to be safe and easy.
    
    client = app.test_client()
    
    # Register
    client.post('/register', data={
        'name': test_name,
        'email': test_email,
        'password': test_password,
        'role': 'student'
    })
    
    # Login
    login_resp = client.post('/login', data={
        'email': test_email,
        'password': test_password,
        'role': 'student'
    })
    
    if login_resp.status_code != 200:
        print(f"[FAILURE] Login failed: {login_resp.get_json()}")
        return

    # 2. Test Adding Study Session
    print("\n[TEST] Adding Study Session...")
    
    # Prepare data
    today = datetime.now().strftime("%Y-%m-%d")
    duration = 120
    topic = "Advanced Python Testing"
    # We might need a skill ID. Let's send without one first (it's nullable in code logic? Let's check routes.py)
    # logic: `skill_id_int = int(skill_id) if skill_id else None` -> Yes nullable.
    
    response = client.post('/student/add-study-session', data={
        'date': today,
        'duration_minutes': duration,
        'topic_studied': topic,
        'related_skill_id': '' 
    }, follow_redirects=True)
    
    # Check if redirect happened (status code 200 after following redirect)
    if response.status_code == 200:
        print("   [SUCCESS] Request completed (Redirect folllowed)")
    else:
        print(f"   [FAILURE] Request failed with status {response.status_code}")
        print(response.data)

    # 3. Verify Database
    print("\n[VERIFY] Checking Database for StudySession...")
    with app.app_context():
        user = User.query.filter_by(email=test_email).first()
        student = StudentProfile.query.filter_by(user_id=user.id).first()
        
        session = StudySession.query.filter_by(student_id=student.id, topic_studied=topic).first()
        
        if session:
            print(f"   [SUCCESS] StudySession found!")
            print(f"   - ID: {session.id}")
            print(f"   - Topic: {session.topic_studied}")
            print(f"   - Duration: {session.duration_minutes} min")
            print(f"   - Date: {session.date}")
        else:
            print("   [FAILURE] StudySession NOT found in database.")

        # Cleanup
        print("\n[CLEANUP] Removing test data...")
        if session: db.session.delete(session)
        if student: db.session.delete(student)
        if user: db.session.delete(user)
        db.session.commit()
        print("   [SUCCESS] Cleanup complete.")

    print("="*60)

if __name__ == "__main__":
    run_verification()
