from app import create_app
from core.extensions import db
from models import TeacherProfile
from dashboard.teacher_routes import get_global_transfer_requests
from models.teacher import AssignmentTransferRequest
from sqlalchemy.orm import joinedload
from flask import render_template
import datetime

app = create_app()
with app.app_context():
    app.config['SERVER_NAME'] = 'localhost'
    with app.test_request_context('/teacher/students'):
        teacher = TeacherProfile.query.get(16)
        outgoing = AssignmentTransferRequest.query.options(
            joinedload(AssignmentTransferRequest.current_owner), 
            joinedload(AssignmentTransferRequest.student)
        ).filter_by(requester_id=teacher.id, status="pending").all()
        
        incoming = AssignmentTransferRequest.query.options(
            joinedload(AssignmentTransferRequest.requester), 
            joinedload(AssignmentTransferRequest.student)
        ).filter_by(current_owner_id=teacher.id, status="pending").all()
        
        html = render_template('teacher_students.html', 
                               teacher=teacher, 
                               overview={}, 
                               students=[], 
                               incoming_requests=incoming, 
                               outgoing_requests=outgoing, 
                               now_date=datetime.datetime.now().strftime("%d %B, %Y"), 
                               global_transfer_requests=[])
        
        if 'Sent Requests (Pending)' in html:
            print("RENDERED OUTGOING")
        else:
            print("FAILED TO RENDER OUTGOING")
            
        teacher2 = TeacherProfile.query.get(2)
        incoming2 = AssignmentTransferRequest.query.options(
            joinedload(AssignmentTransferRequest.requester), 
            joinedload(AssignmentTransferRequest.student)
        ).filter_by(current_owner_id=teacher2.id, status="pending").all()
        
        html2 = render_template('teacher_students.html', 
                               teacher=teacher2, 
                               overview={}, 
                               students=[], 
                               incoming_requests=incoming2, 
                               outgoing_requests=[], 
                               now_date=datetime.datetime.now().strftime("%d %B, %Y"), 
                               global_transfer_requests=[])
        
        if 'Incoming Transfer Requests' in html2:
            print("RENDERED INCOMING")
        else:
            print("FAILED TO RENDER INCOMING")
