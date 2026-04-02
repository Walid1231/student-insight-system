from app import create_app
from core.extensions import db
from models.teacher import AssignmentTransferRequest

app = create_app()
with app.app_context():
    AssignmentTransferRequest.__table__.create(db.engine, checkfirst=True)
    print("Table AssignmentTransferRequest created successfully")
