"""Diagnostic - writes to .md so view_file can read it."""
from app import create_app
from core.extensions import db
from models.teacher import AssignmentTransferRequest, TeacherProfile, TeacherAssignment
from sqlalchemy.orm import joinedload

app = create_app()
with app.app_context():
    lines = []
    
    lines.append("# Transfer Debug Report")
    lines.append("")
    lines.append("## Teachers")
    teachers = TeacherProfile.query.all()
    for t in teachers:
        lines.append(f"- ID={t.id} user_id={t.user_id} name={t.full_name}")

    lines.append("")
    lines.append("## All Transfer Requests")
    all_reqs = AssignmentTransferRequest.query.options(
        joinedload(AssignmentTransferRequest.requester),
        joinedload(AssignmentTransferRequest.current_owner),
        joinedload(AssignmentTransferRequest.student),
    ).all()
    if not all_reqs:
        lines.append("**NO transfer requests exist in the database at all!**")
    for r in all_reqs:
        req_name = r.requester.full_name if r.requester else 'N/A'
        own_name = r.current_owner.full_name if r.current_owner else 'N/A'
        stu_name = r.student.full_name if r.student else 'N/A'
        lines.append(f"- ReqID={r.id} status={r.status} requester={req_name}(id={r.requester_id}) owner={own_name}(id={r.current_owner_id}) student={stu_name}(id={r.student_id})")

    lines.append("")
    lines.append("## Bell Notification Sim")
    for t in teachers:
        incoming = AssignmentTransferRequest.query.filter_by(
            current_owner_id=t.id, status="pending"
        ).all()
        lines.append(f"- {t.full_name} (ID={t.id}): {len(incoming)} incoming pending")

    lines.append("")
    lines.append("## Teacher Assignments")
    assignments = TeacherAssignment.query.all()
    for a in assignments:
        lines.append(f"- AssignID={a.id} teacher_id={a.teacher_id} student_id={a.student_id}")

    with open("debug_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("Done!")
