import os
import sys
import time

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def reset_database():
    print("="*50)
    print("      DATABASE RESET UTILITY")
    print("="*50)
    print("This script will delete the existing database and recreate it")
    print("with the new schema (including University, Target GPA, etc.)")
    print("\nWARNING: ALL EXISTING DATA WILL BE LOST!")
    print("="*50)
    
    db_path = os.path.join(app.root_path, 'instance', 'student_insight_v2.db')
    
    if os.path.exists(db_path):
        print(f"\nFound existing database at: {db_path}")
        try:
            os.remove(db_path)
            print("[SUCCESS] Old database deleted.")
        except PermissionError:
            print("\n[ERROR] Could not delete the database file.")
            print("It is likely being used by the running Flask server.")
            print("\n*** ACTION REQUIRED ***")
            print("1. Please STOP your running Flask server (Ctrl+C in the terminal).")
            print("2. Run this script again.")
            return
    else:
        print(f"\nNo existing database found at {db_path}. Creating new one...")

    # Recreate DB
    with app.app_context():
        print("Creating new database tables...")
        db.create_all()
        print("[SUCCESS] New database created successfully!")
        
    print("\n[INFO] You can now restart your Flask server.")
    print("       Login as a new user and go to /student/dashboard/v2")

if __name__ == "__main__":
    reset_database()
