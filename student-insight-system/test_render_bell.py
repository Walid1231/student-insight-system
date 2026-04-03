"""Test: render teacher_students.html for teacher 'gf' (ID=2) who has 2 pending incoming requests."""
from app import create_app
from core.extensions import db
from models.teacher import AssignmentTransferRequest, TeacherProfile, TeacherAssignment
from models import StudentProfile
from sqlalchemy.orm import joinedload

app = create_app()
with app.app_context():
    teacher = TeacherProfile.query.get(2)  # gf
    
    # Simulate get_global_transfer_requests
    gtrs = AssignmentTransferRequest.query.options(
        joinedload(AssignmentTransferRequest.requester),
        joinedload(AssignmentTransferRequest.student)
    ).filter_by(current_owner_id=teacher.id, status="pending").all()
    
    incoming = AssignmentTransferRequest.query.options(
        joinedload(AssignmentTransferRequest.requester),
        joinedload(AssignmentTransferRequest.student)
    ).filter_by(current_owner_id=teacher.id, status="pending").all()
    
    outgoing = AssignmentTransferRequest.query.options(
        joinedload(AssignmentTransferRequest.current_owner),
        joinedload(AssignmentTransferRequest.student)
    ).filter_by(requester_id=teacher.id, status="pending").all()
    
    students = (
        StudentProfile.query
        .join(TeacherAssignment, TeacherAssignment.student_id == StudentProfile.id)
        .filter(TeacherAssignment.teacher_id == teacher.id)
        .distinct().all()
    )
    
    lines = []
    lines.append(f"Teacher: {teacher.full_name} (ID={teacher.id})")
    lines.append(f"Global transfer requests (bell): {len(gtrs)}")
    lines.append(f"Incoming requests: {len(incoming)}")
    lines.append(f"Outgoing requests: {len(outgoing)}")
    lines.append(f"Assigned students: {len(students)}")
    
    with app.test_request_context('/teacher/students'):
        from flask import render_template
        try:
            html = render_template(
                'teacher_students.html',
                teacher=teacher,
                overview={'total_students': len(students), 'alerts_count': 0},
                students=students,
                incoming_requests=incoming,
                outgoing_requests=outgoing,
                now_date="03 April, 2026",
                global_transfer_requests=gtrs,
            )
            
            if 'has requested to formally transfer' in html:
                lines.append("BELL: descriptive transfer cards RENDERED")
            else:
                lines.append("BELL: descriptive transfer cards NOT rendered")
            
            if 'Incoming Transfer Requests' in html:
                lines.append("PAGE: Incoming Transfer Requests table RENDERED")
            else:
                lines.append("PAGE: Incoming Transfer Requests table NOT rendered")
            
            if 'top-req-card-' in html:
                import re
                card_ids = re.findall(r'top-req-card-(\d+)', html)
                lines.append(f"Bell card IDs: {card_ids}")
            
            if 'req-row-' in html:
                import re
                row_ids = re.findall(r'req-row-(\d+)', html)
                lines.append(f"Table row IDs: {row_ids}")
                
            lines.append("TEMPLATE RENDERED SUCCESSFULLY - NO ERRORS")
        except Exception as e:
            lines.append(f"RENDER ERROR: {e}")
            import traceback
            lines.append(traceback.format_exc())
    
    with open("render_test_results.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("Done!")
