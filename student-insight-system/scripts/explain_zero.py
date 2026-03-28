from app import create_app
from models import db, StudentProfile, StudentSkill, Skill, CareerPath, CareerRequiredSkill
import os

app = create_app()
with app.app_context():
    print("\n--- AHMED AL-RASHID: FULL SKILL PROFILE ---")
    ahmed = StudentProfile.query.filter_by(full_name='Ahmed Al-Rashid').first()
    if ahmed:
        a_skills = StudentSkill.query.filter_by(student_id=ahmed.id).all()
        for ss in a_skills:
            # Join with Skill to see the MASTER record
            master = Skill.query.get(ss.skill_id) if ss.skill_id else None
            m_name = master.skill_name if master else "N/A (Broken Link)"
            print(f"Skill: {ss.skill_name} | ID in Records: {ss.skill_id} | Master Matches: {m_name}")
    
    print("\n--- CAREER: AI / MACHINE LEARNING ENGINEER (ID 35) ---")
    career = CareerPath.query.get(35)
    if career:
        reqs = CareerRequiredSkill.query.filter_by(career_id=career.id).all()
        for r in reqs:
            master = Skill.query.get(r.skill_id)
            print(f"Required: {master.skill_name if master else 'Unknown'} | Master ID: {r.skill_id}")

    # Check for specific name: "Python"
    print("\n--- CHECKING FOR 'Python' IN MASTER CATALOG ---")
    pythons = Skill.query.filter(Skill.skill_name.ilike('python')).all()
    for p in pythons:
        print(f"Master Skill: '{p.skill_name}' (ID: {p.id}) | Dept: {p.department}")
