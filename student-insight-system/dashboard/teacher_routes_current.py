"""
dashboard/teacher_routes.py
============================
All teacher-facing routes and APIs, registered on `teacher_bp` Blueprint.
Register in dashboard/__init__.py:

    from dashboard.teacher_routes import teacher_bp
    app.register_blueprint(teacher_bp)
"""

from flask import Blueprint, render_template, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from models import (
    StudentProfile, TeacherProfile, TeacherAssignment,
    StudentAlert, StudentSkill, StudentNote, StudentAcademicRecord,
    CourseCatalog, StudentGoal, CareerPath, WeeklyUpdate,
    StudentInsight, db,
)
from ml.analytics_engine import AnalyticsEngine
from sqlalchemy import func, case
from sqlalchemy.orm import selectinload, joinedload
from core.extensions import cache
from sqlalchemy.orm import selectinload
from collections import defaultdict
from datetime import datetime
import re

teacher_bp = Blueprint("teacher", __name__)
analytics_engine = AnalyticsEngine()


# ─────────────────────────────────────────────────────────────────────────────
#  Auth helper
# ─────────────────────────────────────────────────────────────────────────────

def _get_teacher_or_403():
    """Authenticate teacher JWT. Returns (teacher, None) or (None, error_response)."""
    claims = get_jwt()
    if claims.get("role") != "teacher":
        return None, (jsonify({"msg": "Access denied"}), 403)
    try:
        user_id = int(get_jwt_identity())
    except (ValueError, TypeError):
        return None, (jsonify({"msg": "Invalid user identity"}), 400)
    teacher = TeacherProfile.query.filter_by(user_id=user_id).first()
    if not teacher:
        return None, (jsonify({"msg": "Teacher profile not found"}), 404)
    return teacher, None


# ─────────────────────────────────────────────────────────────────────────────
#  Page routes
# ─────────────────────────────────────────────────────────────────────────────

@teacher_bp.route("/teacher/dashboard")
@jwt_required()
def teacher_dashboard():
    claims = get_jwt()
    if claims.get("role") != "teacher":
        return jsonify({"msg": "Access denied"}), 403
    try:
        user_id = int(get_jwt_identity())
    except (ValueError, TypeError):
        return jsonify({"msg": "Invalid user identity"}), 400

    teacher = TeacherProfile.query.filter_by(user_id=user_id).first()
    if not teacher:
        return jsonify({"msg": "Teacher profile not found"}), 404

    students = (
        StudentProfile.query
        .join(TeacherAssignment, TeacherAssignment.student_id == StudentProfile.id)
        .filter(TeacherAssignment.teacher_id == teacher.id)
        .distinct()
        .all()
    )
    student_ids = [s.id for s in students]

    alerts = []
    if student_ids:
        alerts = (
            StudentAlert.query
            .filter(
                StudentAlert.student_id.in_(student_ids),
                StudentAlert.is_resolved == False,
            )
            .options(selectinload(StudentAlert.student))
            .order_by(StudentAlert.created_at.desc())
            .limit(20)
            .all()
        )

    if students:
        kpi_row = (
            db.session.query(
                func.count(StudentProfile.id).label("total"),
                func.sum(case((StudentProfile.current_cgpa >= 3.5, 1), else_=0)).label("good"),
                func.sum(case(((StudentProfile.current_cgpa >= 2.5) & (StudentProfile.current_cgpa < 3.5), 1), else_=0)).label("average"),
                func.sum(case(((StudentProfile.current_cgpa != None) & (StudentProfile.current_cgpa < 2.5), 1), else_=0)).label("at_risk"),
            )
            .filter(StudentProfile.id.in_(student_ids))
            .one()
        )
        good_count    = kpi_row.good    or 0
        average_count = kpi_row.average or 0
        at_risk_count = kpi_row.at_risk or 0
        total         = kpi_row.total   or 0
    else:
        good_count = average_count = at_risk_count = total = 0

    overview_data = {
        "total_students":  total,
        "good_count":      good_count,
        "average_count":   average_count,
        "at_risk_count":   at_risk_count,
        "alerts_count":    len(alerts),
        "average_percent": round(average_count / total * 100, 1) if total else 0,
        "good_percent":    round(good_count    / total * 100, 1) if total else 0,
        "at_risk_percent": round(at_risk_count / total * 100, 1) if total else 0,
        "class_distribution":   {},
        "section_distribution": {},
    }

    return render_template(
        "teacher_dashboard.html",
        teacher=teacher,
        overview=overview_data,
        alerts=alerts,
        now_date=datetime.now().strftime("%d %B, %Y"),
    )


@teacher_bp.route("/teacher/students")
@jwt_required()
def teacher_students_page():
    teacher, err = _get_teacher_or_403()
    if err:
        return err

    page = request.args.get('page', 1, type=int)

    students_query = (
        StudentProfile.query
        .join(TeacherAssignment, TeacherAssignment.student_id == StudentProfile.id)
        .filter(TeacherAssignment.teacher_id == teacher.id)
        .distinct()
    )
    
    pagination = students_query.paginate(page=page, per_page=25, error_out=False)
    students = pagination.items

    student_ids = [s.id for s in students]

    alerts_count = 0
    if student_ids:
        alerts_count = (
            StudentAlert.query
            .filter(
                StudentAlert.student_id.in_(student_ids),
                StudentAlert.is_resolved == False,
            )
            .count()
        )

    overview_data = {
        "total_students": pagination.total,
        "alerts_count":   alerts_count,
    }

    return render_template(
        "teacher_students.html",
        teacher=teacher,
        overview=overview_data,
        students=students,
        pagination=pagination,
        now_date=datetime.now().strftime("%d %B, %Y"),
    )


@teacher_bp.route("/teacher/alerts")
@jwt_required()
def teacher_alerts_page():
    teacher, err = _get_teacher_or_403()
    if err:
        return err

    student_ids = [
        a.student_id for a in
        TeacherAssignment.query.filter_by(teacher_id=teacher.id).all()
    ]

    # Get page number from request args, default to 1
    page = request.args.get("page", 1, type=int)

    alerts_pagination = None
    if student_ids:
        alerts_pagination = (
            StudentAlert.query
            .filter(
                StudentAlert.student_id.in_(student_ids),
                StudentAlert.is_resolved == False,
            )
            .options(selectinload(StudentAlert.student))
            .order_by(StudentAlert.created_at.desc())
            .paginate(page=page, per_page=20, error_out=False)
        )

    alerts = alerts_pagination.items if alerts_pagination else []
    
    # Calculate total alerts for sidebar badge
    total_alerts_count = alerts_pagination.total if alerts_pagination else 0
    has_next = alerts_pagination.has_next if alerts_pagination else False

    # IF the request is an AJAX/fetch call for infinite scroll, return JSON
    if request.headers.get("Accept") == "application/json" or request.args.get("json") == "true":
        return jsonify({
            "alerts": [
                {
                    "id": a.id,
                    "student_name": a.student.full_name if a.student else "Unknown",
                    "type": a.type,
                    "severity": a.severity,
                    "message": a.message,
                    "created_at": a.created_at.strftime('%b %d, %Y'),
                    "is_resolved": a.is_resolved
                } for a in alerts
            ],
            "has_next": has_next,
            "next_page": page + 1 if has_next else None,
            "total_alerts": total_alerts_count
        })

    return render_template(
        "teacher_alerts.html",
        teacher=teacher,
        alerts=alerts,
        total_alerts=total_alerts_count,
        has_next=has_next,
        next_page=page + 1 if has_next else None,
        now_date=datetime.now().strftime("%d %B, %Y"),
    )


@teacher_bp.route("/teacher/student/<int:student_id>")
@jwt_required()
def teacher_student_detail(student_id):
    claims = get_jwt()
    if claims.get("role") != "teacher":
        return jsonify({"success": False, "msg": "Access denied"}), 403
    try:
        user_id = int(get_jwt_identity())
    except (ValueError, TypeError):
        return jsonify({"success": False, "msg": "Invalid user identity"}), 400

    teacher = TeacherProfile.query.filter_by(user_id=user_id).first()
    if not teacher:
        return jsonify({"success": False, "msg": "Teacher profile not found"}), 404

    assignment = TeacherAssignment.query.filter_by(
        teacher_id=teacher.id, student_id=student_id
    ).first()
    if not assignment:
        return jsonify({"success": False, "msg": "You are not assigned to this student"}), 403

    student = StudentProfile.query.options(
        joinedload(StudentProfile.skills),
        joinedload(StudentProfile.student_goals),
        joinedload(StudentProfile.weekly_updates)
    ).get(student_id)
    
    if not student:
        return jsonify({"success": False, "msg": "Student not found"}), 404

    from dashboard.student_stats import (
        calculate_attendance_stats,
        calculate_assignment_stats,
        calculate_assessment_stats,
        calculate_performance_trend,
    )
    attendance        = calculate_attendance_stats(student_id)
    assignments_data  = calculate_assignment_stats(student_id)
    assessments       = calculate_assessment_stats(student_id)
    performance_trend = calculate_performance_trend(student_id)

    days_since_active = None
    if student.last_activity:
        days_since_active = (datetime.utcnow() - student.last_activity).days

    notes = StudentNote.query.filter_by(
        student_id=student_id, teacher_id=teacher.id
    ).order_by(StudentNote.created_at.desc()).all()

    # A) Profile summary
    profile_summary = {
        "full_name":          student.full_name,
        "department":         student.department or "—",
        "class_level":        student.class_level or "—",
        "section":            student.section or "—",
        "current_cgpa":       student.current_cgpa,
        "target_cgpa":        student.target_cgpa,
        "performance_status": student.performance_status,
    }

    # B) Academic snapshot
    records_raw = (
        db.session.query(StudentAcademicRecord, CourseCatalog)
        .join(CourseCatalog, StudentAcademicRecord.course_id == CourseCatalog.id)
        .filter(StudentAcademicRecord.student_id == student_id)
        .all()
    )
    semesters = defaultdict(list)
    for r, c in records_raw:
        semesters[r.semester_taken].append((r.grade_point or 0.0, c.credit_value or 3))

    semester_gpa_trend = []
    total_credits = 0
    for sem in sorted(semesters.keys()):
        grades = semesters[sem]
        sem_cr = sum(cr for _, cr in grades)
        sem_gpa = round(sum(gp * cr for gp, cr in grades) / sem_cr, 2) if sem_cr > 0 else 0.0
        semester_gpa_trend.append((f"Sem {sem}", sem_gpa))
        total_credits += sem_cr

    # Cached AI Prediction
    @cache.memoize(timeout=600)
    def get_predicted_gpa(sid):
        try:
            return round(analytics_engine.predict_next_gpa(sid), 2)
        except Exception:
            return None

    predicted_gpa = get_predicted_gpa(student_id)

    academic_snapshot = {
        "predicted_next_gpa": predicted_gpa,
        "total_credits":      total_credits,
        "semester_trend":     semester_gpa_trend[-3:],
    }

    # C) Skill snapshot
    top_risk_skills = sorted(student.skills, key=lambda s: s.risk_score or 0, reverse=True)[:3]
    skill_snapshot = [
        {
            "skill_name":        s.skill_name,
            "proficiency_score": s.proficiency_score,
            "risk_score":        round(s.risk_score * 100) if s.risk_score else 0,
        }
        for s in top_risk_skills
    ]

    # D) Weekly snapshot
    latest_update = sorted(student.weekly_updates, key=lambda w: w.created_at, reverse=True)
    latest_update = latest_update[0] if latest_update else None
    
    weekly_snapshot = None
    if latest_update:
        weekly_snapshot = {
            "total_hours_studied":    latest_update.total_hours_studied or 0,
            "burnout_risk_pct":       int((latest_update.burnout_risk_score or 0) * 100),
            "goal_achievability_pct": int((latest_update.goal_achievability_prob or 0) * 100),
            "status_label":           latest_update.status_label or "N/A",
        }

    # E) Career snapshot
    primary_goal = next((g for g in student.student_goals if g.is_primary), None)
    career_snapshot = None
    if primary_goal:
        cp = CareerPath.query.get(primary_goal.career_id)
        if cp:
            career_snapshot = {
                "career_title": cp.title,
                "goal_type":    primary_goal.goal_type or "Long Term",
            }

    # F) AI insight preview
    latest_insight = (
        StudentInsight.query
        .filter_by(student_id=student_id)
        .order_by(StudentInsight.generated_at.desc())
        .first()
    )
    insight_preview = None
    if latest_insight:
        plain_text = re.sub(r'<[^>]+>', '', latest_insight.content or '')
        plain_text = ' '.join(plain_text.split())
        insight_preview = {
            "preview_text": plain_text[:300] + ("…" if len(plain_text) > 300 else ""),
            "generated_at": latest_insight.generated_at,
            "insight_id":   latest_insight.id,
        }

    return render_template(
        "student_detail.html",
        teacher=teacher,
        student=student,
        attendance=attendance,
        assignments=assignments_data,
        assessments=assessments,
        performance_trend=performance_trend,
        days_since_active=days_since_active,
        notes=notes,
        insight=latest_insight,
        profile_summary=profile_summary,
        academic_snapshot=academic_snapshot,
        skill_snapshot=skill_snapshot,
        weekly_snapshot=weekly_snapshot,
        career_snapshot=career_snapshot,
        insight_preview=insight_preview,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Teacher API endpoints
# ─────────────────────────────────────────────────────────────────────────────

@teacher_bp.route("/api/teacher/students", methods=["GET"])
@jwt_required()
def api_teacher_students():
    teacher, err = _get_teacher_or_403()
    if err:
        return err

    class_filter   = request.args.get("class")
    section_filter = request.args.get("section")
    status_filter  = request.args.get("status")
    search_query   = (request.args.get("search") or "").strip()

    query = (
        db.session.query(StudentProfile)
        .join(TeacherAssignment)
        .filter(TeacherAssignment.teacher_id == teacher.id)
    )
    if class_filter:
        query = query.filter(StudentProfile.class_level == class_filter)
    if section_filter:
        query = query.filter(StudentProfile.section == section_filter)
    if search_query:
        like_term = f"%{search_query}%"
        query = query.filter(
            db.or_(
                StudentProfile.student_code.ilike(like_term),
                StudentProfile.full_name.ilike(like_term),
            )
        )

    pagination = query.distinct().paginate(page=request.args.get('page', 1, type=int), per_page=25, error_out=False)
    students = pagination.items
    result = []
    for s in students:
        if status_filter and s.performance_status != status_filter:
            continue
        result.append({
            "id":           s.id,
            "name":         s.full_name,
            "student_code": s.student_code,
            "class_level":  s.class_level,
            "section":      s.section,
            "cgpa":         s.current_cgpa,
            "status":       s.performance_status,
            "last_active":  s.last_active.isoformat() if hasattr(s, "last_active") and s.last_active else None,
        })
    return jsonify({"success": True, "students": result, "total": pagination.total})


@teacher_bp.route("/api/teacher/notes", methods=["POST"])
@jwt_required()
def api_teacher_add_note():
    teacher, err = _get_teacher_or_403()
    if err:
        return err

    body       = request.get_json(silent=True) or {}
    student_id = body.get("student_id")
    content    = (body.get("content") or "").strip()

    if not student_id or not content:
        return jsonify({"success": False, "msg": "student_id and content are required"}), 400

    assigned = TeacherAssignment.query.filter_by(
        teacher_id=teacher.id, student_id=int(student_id)
    ).first()
    if not assigned:
        return jsonify({"success": False, "msg": "Student not in your assignment scope"}), 403

    from models import StudentNote
    note = StudentNote(
        student_id=int(student_id), teacher_id=teacher.id,
        content=content, is_private=True,
    )
    db.session.add(note)
    db.session.commit()
    
    return jsonify({
        "success": True, 
        "note": {
            "id": note.id, 
            "content": note.content, 
            "created_at": note.created_at.isoformat() if note.created_at else datetime.now().isoformat()
        }
    }), 201

@teacher_bp.route("/api/teacher/notes/<int:note_id>", methods=["DELETE"])
@jwt_required()
def api_teacher_delete_note(note_id):
    teacher, err = _get_teacher_or_403()
    if err:
        return err

    from models import StudentNote
    note = StudentNote.query.get(note_id)
    if not note:
        return jsonify({"success": False, "msg": "Note not found"}), 404

    if note.teacher_id != teacher.id:
        return jsonify({"success": False, "msg": "You do not have permission to delete this note"}), 403

    db.session.delete(note)
    db.session.commit()
    return jsonify({"success": True, "msg": "Note deleted"})


@teacher_bp.route("/api/teacher/alerts/<int:alert_id>/resolve", methods=["POST"])
@jwt_required()
def api_resolve_alert(alert_id):
    teacher, err = _get_teacher_or_403()
    if err:
        return err

    # Require application/json content type for security against CSRF
    if not request.is_json:
        return jsonify({"success": False, "msg": "Content-Type must be application/json"}), 400

    alert = (
        StudentAlert.query
        .join(TeacherAssignment, TeacherAssignment.student_id == StudentAlert.student_id)
        .filter(
            StudentAlert.id == alert_id,
            TeacherAssignment.teacher_id == teacher.id,
        )
        .first()
    )
    if not alert:
        return jsonify({"success": False, "msg": "Alert not found or not in your scope"}), 404

    alert.is_resolved = True
    db.session.commit()
    return jsonify({"success": True, "msg": "Alert resolved"})


@teacher_bp.route("/api/teacher/alerts/resolve-batch", methods=["POST"])
@jwt_required()
def api_resolve_alerts_batch():
    teacher, err = _get_teacher_or_403()
    if err:
        return err

    # Require application/json content type
    if not request.is_json:
        return jsonify({"success": False, "msg": "Content-Type must be application/json"}), 400

    data = request.get_json()
    alert_ids = data.get("alert_ids", [])
    
    if not alert_ids or not isinstance(alert_ids, list):
        return jsonify({"success": False, "msg": "Valid 'alert_ids' list is required"}), 400

    try:
        # Filter alerts that belong to this teacher's students and are unresolved
        alerts_to_resolve = (
            StudentAlert.query
            .join(TeacherAssignment, TeacherAssignment.student_id == StudentAlert.student_id)
            .filter(
                TeacherAssignment.teacher_id == teacher.id,
                StudentAlert.id.in_(alert_ids),
                StudentAlert.is_resolved == False
            )
            .all()
        )
        
        resolved_count = 0
        resolved_ids = []
        for alert in alerts_to_resolve:
            alert.is_resolved = True
            resolved_ids.append(alert.id)
            resolved_count += 1
            
        db.session.commit()
        
        failed_ids = list(set(alert_ids) - set(resolved_ids))
        
        return jsonify({
            "success": True, 
            "resolved_count": resolved_count,
            "failed_ids": failed_ids
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "msg": "Internal Server Error"}), 500


@teacher_bp.route("/api/teacher/alerts/summary", methods=["GET"])
@jwt_required()
def api_teacher_alerts_summary():
    """
    Returns a JSON count of unresolved alerts grouped by severity 
    for the logged-in teacher's assigned students.
    """
    teacher, err = _get_teacher_or_403()
    if err:
        return err
        
    try:
        summary_data = (
            db.session.query(
                StudentAlert.severity, 
                func.count(StudentAlert.id).label('count')
            )
            .join(TeacherAssignment, TeacherAssignment.student_id == StudentAlert.student_id)
            .filter(
                TeacherAssignment.teacher_id == teacher.id,
                StudentAlert.is_resolved == False
            )
            .group_by(StudentAlert.severity)
            .all()
        )
        
        result = {severity: count for severity, count in summary_data}
        
        return jsonify({
            "success": True,
            "total": sum(result.values()),
            "breakdown": result
        }), 200
    except Exception as e:
        return jsonify({"success": False, "msg": "Internal Server Error"}), 500


@teacher_bp.route("/api/teacher/class-skills", methods=["GET"])
@jwt_required()
def api_teacher_class_skills():
    teacher, err = _get_teacher_or_403()
    if err:
        return err

    rows = (
        db.session.query(
            StudentProfile.id.label("student_id"),
            StudentProfile.full_name.label("student_name"),
            StudentSkill.skill_name,
            StudentSkill.proficiency_score,
            StudentSkill.risk_score,
        )
        .join(TeacherAssignment, TeacherAssignment.student_id == StudentProfile.id)
        .join(StudentSkill, StudentSkill.student_id == StudentProfile.id)
        .filter(TeacherAssignment.teacher_id == teacher.id)
        .order_by(StudentProfile.id, StudentSkill.proficiency_score.desc())
        .all()
    )

    result: dict = {}
    for row in rows:
        if row.student_id not in result:
            result[row.student_id] = {
                "student_id": row.student_id,
                "name":       row.student_name,
                "skills":     [],
            }
        result[row.student_id]["skills"].append({
            "name":  row.skill_name,
            "score": row.proficiency_score,
            "risk":  row.risk_score,
        })

    return jsonify(list(result.values()))


@teacher_bp.route("/api/teacher/unassigned-students", methods=["GET"])
@jwt_required()
def api_unassigned_students():
    """Return all StudentProfile rows NOT assigned to the current teacher."""
    teacher, err = _get_teacher_or_403()
    if err:
        return err

    search_query = (request.args.get("search") or "").strip()

    already_assigned = (
        db.session.query(TeacherAssignment.student_id)
        .filter_by(teacher_id=teacher.id)
        .subquery()
    )
    
    query = StudentProfile.query.filter(StudentProfile.id.notin_(already_assigned))
    
    if search_query:
        like_term = f"%{search_query}%"
        query = query.filter(
            db.or_(
                StudentProfile.student_code.ilike(like_term),
                StudentProfile.full_name.ilike(like_term),
                StudentProfile.department.ilike(like_term),
                StudentProfile.class_level.ilike(like_term)
            )
        )
        
    students = query.order_by(StudentProfile.full_name).all()

    return jsonify([
        {
            "id":                 s.id,
            "full_name":          s.full_name,
            "student_code":       s.student_code,
            "department":         s.department or "—",
            "class_level":        s.class_level or "—",
            "section":            s.section or "—",
            "current_cgpa":       round(float(s.current_cgpa), 2) if s.current_cgpa else None,
            "performance_status": s.performance_status,
        }
        for s in students
    ])


@teacher_bp.route("/api/teacher/assign-student", methods=["POST"])
@jwt_required()
def api_teacher_assign_student():
    """Create a TeacherAssignment row linking this teacher to a student."""
    teacher, err = _get_teacher_or_403()
    if err:
        return err

    data       = request.get_json(silent=True) or {}
    student_id = data.get("student_id")
    if not student_id:
        return jsonify({"success": False, "msg": "student_id is required"}), 400

    # Enforce max 50 students
    current_count = TeacherAssignment.query.filter_by(teacher_id=teacher.id).count()
    if current_count >= 50:
        return jsonify({"success": False, "msg": "Assignment limit of 50 students exceeded"}), 400

    student = StudentProfile.query.get(int(student_id))
    if not student:
        return jsonify({"success": False, "msg": "Student not found"}), 404

    existing = TeacherAssignment.query.filter_by(
        teacher_id=teacher.id, student_id=student.id
    ).first()
    if existing:
        return jsonify({"success": False, "msg": "Student is already assigned to you"}), 409

    db.session.add(TeacherAssignment(
        teacher_id=teacher.id, student_id=student.id,
        assignment_type="homeroom",
    ))
    db.session.commit()

    return jsonify({
        "success": True,
        "assigned_student": {
            "id":                 student.id,
            "full_name":          student.full_name,
            "student_code":       student.student_code,
            "department":         student.department or "—",
            "class_level":        student.class_level or "—",
            "section":            student.section or "—",
            "current_cgpa":       round(float(student.current_cgpa), 2) if student.current_cgpa else None,
            "performance_status": student.performance_status,
        },
    }), 201


@teacher_bp.route("/api/teacher/unassign-student", methods=["DELETE"])
@jwt_required()
def api_teacher_unassign_student():
    """Remove a TeacherAssignment row for the current teacher."""
    teacher, err = _get_teacher_or_403()
    if err:
        return err

    data       = request.get_json(silent=True) or {}
    student_id = data.get("student_id")
    if not student_id:
        return jsonify({"success": False, "msg": "student_id is required"}), 400

    assignment = TeacherAssignment.query.filter_by(
        teacher_id=teacher.id, student_id=int(student_id)
    ).first()
    if not assignment:
        return jsonify({"success": False, "msg": "Assignment not found or does not belong to you"}), 403

    db.session.delete(assignment)
    db.session.commit()
    return jsonify({"success": True, "msg": "Student unassigned"})


@teacher_bp.route("/api/teacher/unassign-students-batch", methods=["DELETE"])
@jwt_required()
def api_teacher_unassign_students_batch():
    teacher, err = _get_teacher_or_403()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    student_ids = data.get("student_ids", [])
    
    if not student_ids or not isinstance(student_ids, list):
        return jsonify({"success": False, "msg": "Valid 'student_ids' list is required"}), 400

    try:
        assignments_to_remove = (
            TeacherAssignment.query
            .filter(
                TeacherAssignment.teacher_id == teacher.id,
                TeacherAssignment.student_id.in_(student_ids)
            )
            .all()
        )
        
        removed_count = 0
        removed_ids = []
        for assgn in assignments_to_remove:
            db.session.delete(assgn)
            removed_ids.append(assgn.student_id)
            removed_count += 1
            
        db.session.commit()
        
        failed_ids = list(set(student_ids) - set(removed_ids))
        
        return jsonify({
            "success": True, 
            "removed_count": removed_count,
            "failed_ids": failed_ids
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "msg": "Internal Server Error"}), 500
