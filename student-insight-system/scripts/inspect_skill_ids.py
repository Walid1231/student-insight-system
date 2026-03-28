from app import create_app
from models import db, Skill
import os

app = create_app()
with app.app_context():
    ids = [1, 2, 3, 4, 15, 11, 12, 25, 118, 119, 120]
    for sid in ids:
        s = Skill.query.get(sid)
        if s:
            print(f"ID {s.id}: [{s.skill_name}] (Dept: {s.department})")
        else:
            print(f"ID {sid}: NOT FOUND")
