from app import create_app
from models import db, Skill
import os

app = create_app()
with app.app_context():
    print("--- SKILL TABLE TOTAL COUNT ---")
    count = db.session.query(Skill).count()
    print(f"Total count: {count}")
    
    # Dump just the IDs
    ids = [s.id for s in db.session.query(Skill.id).all()]
    print(f"Skill IDs: {ids}")
    
    # Check for ID 1 specifically
    s1 = db.session.query(Skill).get(1)
    if s1:
        print(f"ID 1: '{s1.skill_name}' (found via .get())")
    else:
        print("ID 1: NOT FOUND via .get()")
