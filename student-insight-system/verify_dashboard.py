from app import app
from flask_jwt_extended import create_access_token
from models import User, StudentProfile, db

def verify_dashboard():
    with app.app_context():
        print("VERIFYING DASHBOARD INTEGRATION...")
        
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
        
        # 3. Test Dashboard Page
        print("\nTesting /student/dashboard...")
        res = client.get("/student/dashboard")
        
        if res.status_code == 200:
            print("SUCCESS: Dashboard loaded.")
            content = res.data.decode('utf-8')
            
            # Check for new links
            if "CV Generator" in content:
                print("Element Check 'CV Generator': PASSED")
            else:
                print("Element Check 'CV Generator': FAILED")
                
            if "AI Insight Report" in content:
                print("Element Check 'AI Insight Report': PASSED")
            else:
                print("Element Check 'AI Insight Report': FAILED")
                
            if "/create-profile" in content:
                print("Link Check '/create-profile': PASSED")
            else:
                 print("Link Check '/create-profile': FAILED")
                 
            if "/student/insight-report" in content:
                print("Link Check '/student/insight-report': PASSED")
            else:
                 print("Link Check '/student/insight-report': FAILED")

        else:
            print(f"FAILURE: Dashboard status {res.status_code}")
            
        # 4. Access new pages to ensure they are reachable
        print("\nTesting Access to New Features...")
        
        # CV
        res_cv = client.get("/create-profile")
        if res_cv.status_code == 200:
             print("Access Check /create-profile: PASSED")
        else:
             print(f"Access Check /create-profile: FAILED ({res_cv.status_code})")
             
        # Insight
        res_insight = client.get("/student/insight-report")
        if res_insight.status_code == 200:
             print("Access Check /student/insight-report: PASSED")
        else:
             print(f"Access Check /student/insight-report: FAILED ({res_insight.status_code})")

if __name__ == "__main__":
    verify_dashboard()
