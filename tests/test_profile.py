
import sys
import os
import unittest
from io import BytesIO

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User, StudentProfile
from werkzeug.security import generate_password_hash

class TestProfile(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False 
        app.config['JWT_COOKIE_CSRF_PROTECT'] = False # Disable CSRF for JWT in tests
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create a user
        self.user = User(name="Test Student", email="test@student.com", password=generate_password_hash("password"), role="student")
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self):
        return self.app.post('/login', json={
            "email": "test@student.com",
            "password": "password"
        })

    def test_profile_access(self):
        self.login()
        response = self.app.get('/student/profile')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Student', response.data)

    def test_profile_update(self):
        self.login()
        update_data = {
            "university": "Test Admin Uni",
            "department": "Physics",
            "introduction": "Hello World",
            "linkedin": "https://linkedin.com/in/test"
        }
        response = self.app.post('/student/profile', data=update_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify in DB
        student = StudentProfile.query.filter_by(user_id=self.user.id).first()
        self.assertEqual(student.university, "Test Admin Uni")
        self.assertEqual(student.department, "Physics")
        self.assertEqual(student.introduction, "Hello World")
        self.assertEqual(student.linkedin_link, "https://linkedin.com/in/test")

if __name__ == '__main__':
    unittest.main()
