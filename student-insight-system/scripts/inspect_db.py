from app import create_app
from models import db
from sqlalchemy import inspect
import logging

# Disable distracting logs
logging.getLogger('app').setLevel(logging.ERROR)

app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    tables = ['student_profile', 'student_note', 'teacher_profile', 'weekly_update', 'weekly_updates']
    for table in tables:
        if table in inspector.get_table_names():
            cols = [c['name'] for c in inspector.get_columns(table)]
            print(f"{table}: {cols}")
        else:
            print(f"{table} NOT FOUND")
