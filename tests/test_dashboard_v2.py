
import sys
import os
import unittest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User

class TestDashboardV2(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False 
        
        # IMPORTANT: Use the same cookie configuration as production
        app.config['JWT_TOKEN_LOCATION'] = ['cookies']
        app.config['JWT_COOKIE_CSRF_PROTECT'] = False
        
        self.app = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        db.create_all()
        
        # Create user
        self.user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "password",
            "role": "student"
        }
        self.app.post('/register', json=self.user_data)
        
        # Login (Cookies are automatically handled by test_client)
        resp = self.app.post('/login', json={"email": "test@example.com", "password": "password"})
        if resp.status_code != 200:
            raise Exception("Login failed in setup")

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_update_progress_empty_fields_crash(self):
        """Test if submitting empty strings for numeric fields causes a crash"""
        # Data with empty strings for numeric fields (simulating empty inputs)
        data = {
            "university": "Test Uni",
            "department": "CS",
            "year": "1st",
            "current_cgpa": "3.5", # Valid
            "target_gpa": "",      # Empty string (should crash float conversion)
            "subject_1": "Math",
            "score_1": "",         # Empty string
            "role_1": "Dev",
            "match_1": "",         # Empty string
            "h_mon": "",           # Empty string
            "h_tue": "2",          # Valid
        }
        
        try:
            resp = self.app.post('/update-progress', data=data)
            print(f"Response Status: {resp.status_code}")
            if resp.status_code == 500:
                print("Confirmed: 500 Error received (likely ValueError)")
            else:
                print(f"Unexpected status: {resp.status_code}")
        except ValueError as e:
            print(f"Caught expected ValueError: {e}")
        except Exception as e:
             print(f"Caught unexpected Exception: {e}")

if __name__ == '__main__':
    unittest.main()
