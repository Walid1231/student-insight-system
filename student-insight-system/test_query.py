from app import create_app
from core.extensions import db
from models.teacher import AssignmentTransferRequest
from sqlalchemy.orm import joinedload

app = create_app()
with app.app_context():
    incoming_requests = (
        AssignmentTransferRequest.query
        .options(joinedload(AssignmentTransferRequest.requester), joinedload(AssignmentTransferRequest.student))
        .all()
    )
    print("Fetched", len(incoming_requests))
