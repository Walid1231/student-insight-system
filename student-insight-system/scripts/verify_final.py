from app import create_app
from models import db, StudentProfile, StudentGoal, CareerRequiredSkill, StudentSkill
from services.dashboard_service import DashboardService
import json

app = create_app()
with app.app_context():
    print("\n--- VERIFYING MATCHING SCORE ---")
    
    # Ahmed Al-Rashid
    student = StudentProfile.query.filter_by(full_name="Ahmed Al-Rashid").first()
    if not student:
        print("Student Ahmed Al-Rashid not found")
        exit()
        
    # Get high-level compatibility data
    data = DashboardService.get_dashboard_data(student.user_id)
    compatibility = data.get("compatibility", [])
    
    print(f"Student: {student.full_name}")
    print(f"Skills: {[s.skill_name for s in StudentSkill.query.filter_by(student_id=student.id).all()]}")
    
    print("\nCompatibility Results:")
    for c in compatibility:
        print(f"  {c['role']}: {c['match']}% (Matches: {c['matched_count']}, Required: {c['required_count']})")
    
    print("\n--- TEST COMPLETE ---")
