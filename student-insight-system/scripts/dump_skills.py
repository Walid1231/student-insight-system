from app import create_app
from models import db, Skill
import os

app = create_app()
with app.app_context():
    print("--- FULL SKILL TABLE DUMP ---")
    all_skills = Skill.query.order_by(Skill.id).all()
    print(f"Total count from count(): {Skill.query.count()}")
    print(f"Total count from all(): {len(all_skills)}")
    
    for s in all_skills:
        print(f"ID {s.id}: '{s.skill_name}'")
