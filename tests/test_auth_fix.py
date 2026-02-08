import sys
import os
import json

# Add the project root to the path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User

def run_tests():
    print("Running manual test setup...")
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        
        test_client = app.test_client()
        
        try:
            # 1. Register
            print("\n[TEST] Testing Registration...")
            user_data = {
                "name": "Test Student",
                "email": "test@student.com",
                "password": "securepassword123",
                "role": "student"
            }
            resp = test_client.post('/register', json=user_data)
            print(f"Register status: {resp.status_code}")
            print(f"Register response: {resp.get_json()}")
            
            if resp.status_code == 201:
                print("[PASS] Registration Successful")
            else:
                print("[FAIL] Registration Failed")

            # 2. Login
            print("\n[TEST] Testing Login...")
            login_data = {"email": "test@student.com", "password": "securepassword123"}
            resp_login = test_client.post('/login', json=login_data)
            print(f"Login status: {resp_login.status_code}")
            print(f"Login response: {resp_login.get_json()}")

            if resp_login.status_code == 200:
                print("[PASS] Login Successful")
            else:
                print("[FAIL] Login Failed")
                
            # 3. Invalid Login
            print("\n[TEST] Testing Invalid Login...")
            invalid_data = {"email": "test@student.com", "password": "wrongpassword"}
            resp_fail = test_client.post('/login', json=invalid_data)
            
            if resp_fail.status_code == 401:
                 print("[PASS] Invalid Login correctly rejected")
            else:
                print(f"[FAIL] Invalid Login NOT rejected ({resp_fail.status_code})")

        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    run_tests()
