from app import create_app
from core.extensions import db
from models.teacher import AssignmentTransferRequest

app = create_app()
with app.app_context():
    requests = AssignmentTransferRequest.query.all()
    if not requests:
        print("NO REQUESTS FOUND IN DB")
    for r in requests:
        print(f"Request ID: {r.id}, Requester: {r.requester_id}, Owner: {r.current_owner_id}, Student: {r.student_id}, Status: {r.status}")
