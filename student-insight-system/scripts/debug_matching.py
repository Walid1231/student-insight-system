from app import create_app
from models import db, CareerPath, Skill, CareerRequiredSkill, StudentSkill, StudentProfile
import os

app = create_app()
with app.app_context():
    print("\n--- SYSTEM CAREER PATHS & SKILLS ---")
    c_list = CareerPath.query.all()
    for c in c_list:
        # Join with Skill to get names
        req_kills = db.session.query(Skill.skill_name, Skill.id).join(CareerRequiredSkill).filter(CareerRequiredSkill.career_id == c.id).all()
        print(f"ID {c.id}: {c.title} -> {[r[0] for r in req_kills]}")

    print("\n--- ALL STUDENTS AND THEIR SKILLS ---")
    students = StudentProfile.query.all()
    for s in students:
        s_skills = StudentSkill.query.filter_by(student_id=s.id).all()
        skill_data = [f"{ss.skill_name} (ID: {ss.skill_id})" for ss in s_skills]
        print(f"Student {s.id}: {s.full_name} -> {skill_data}")
