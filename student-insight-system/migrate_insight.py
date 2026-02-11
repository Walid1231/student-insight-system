from app import app, db
from models import StudentInsight

with app.app_context():
    # Helper to check if table exists
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    if 'student_insight' not in inspector.get_table_names():
        print("Creating student_insight table...")
        StudentInsight.__table__.create(db.engine)
        print("Done.")
    else:
        print("Table student_insight already exists.")
