from app import create_app
from models import db, Skill, StudentSkill, CareerRequiredSkill, CareerPath, StudentProfile
import os

app = create_app()
with app.app_context():
    # 1. Check for duplicate skills by name
    print("\n--- CHECKING FOR DUPLICATE SKILLS ---")
    all_skills = Skill.query.all()
    name_map = {}
    for s in all_skills:
        name_lower = s.skill_name.lower()
        if name_lower not in name_map:
            name_map[name_lower] = []
        name_map[name_lower].append(s.id)
    
    for name, ids in name_map.items():
        if len(ids) > 1:
            print(f"Duplicate Skill: {name} -> IDs: {ids}")

    # 2. Check student skills for Ahmed Al-Rashid
    print("\n--- AHMED AL-RASHID SKILLS ---")
    ahmed = StudentProfile.query.filter_by(full_name='Ahmed Al-Rashid').first()
    if ahmed:
        a_skills = StudentSkill.query.filter_by(student_id=ahmed.id).all()
        for s in a_skills:
            print(f"Student Skill: {s.skill_name} (ID: {s.skill_id})")
    
    # 3. Check Career Requirements for AI / ML
    print("\n--- AI ENGINEER REQUIREMENTS ---")
    career = CareerPath.query.filter(CareerPath.title.ilike('%AI%')).first()
    if career:
        print(f"Career: {career.title} (ID: {career.id})")
        reqs = CareerRequiredSkill.query.filter_by(career_id=career.id).all()
        for r in reqs:
            s = Skill.query.get(r.skill_id)
            print(f"Required Skill: {s.skill_name} (Skill ID: {s.id})")

    # 4. Check actual matching logic
    if ahmed and career:
        a_skill_ids = [s.skill_id for s in a_skills]
        req_skill_ids = [r.skill_id for r in reqs]
        matches = set(a_skill_ids).intersection(set(req_skill_ids))
        print(f"\nManual Match Check:")
        print(f"  Student IDs: {a_skill_ids}")
        print(f"  Required IDs: {req_skill_ids}")
        print(f"  Matches Found: {matches}")
