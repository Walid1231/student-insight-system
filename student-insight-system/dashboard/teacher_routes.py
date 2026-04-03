"""
dashboard/teacher_routes.py
============================
All teacher-facing routes and APIs, registered on `teacher_bp` Blueprint.
Register in dashboard/__init__.py:

    from dashboard.teacher_routes import teacher_bp
    app.register_blueprint(teacher_bp)
"""

from flask import Blueprint, render_template, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from models import (
    StudentProfile, TeacherProfile, TeacherAssignment,
    StudentAlert, StudentSkill, StudentNote, StudentAcademicRecord,
    CourseCatalog, StudentGoal, CareerPath, WeeklyUpdate,
    StudentInsight, db,
)
from ml.analytics_engine import AnalyticsEngine
from sqlalchemy import func, case
from sqlalchemy.orm import selectinload
from collections import defaultdict
from services.dashboard_service import DashboardService
from datetime import datetime
import re
import os
import uuid
from werkzeug.utils import secure_filename

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

def get_global_transfer_requests(teacher):
    from models.teacher import AssignmentTransferRequest
    from sqlalchemy.orm import joinedload
    return AssignmentTransferRequest.query.options(
        joinedload(AssignmentTransferRequest.requester), 
        joinedload(AssignmentTransferRequest.student)
    ).filter_by(current_owner_id=teacher.id, status="pending").all()


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

    # ── Avg performance percent (class average CGPA as %) ──
    avg_cgpa = 0.0
    if student_ids:
        avg_row = db.session.query(func.avg(StudentProfile.current_cgpa)).filter(
            StudentProfile.id.in_(student_ids),
            StudentProfile.current_cgpa != None
        ).scalar()
        avg_cgpa = round(float(avg_row), 2) if avg_row else 0.0
    avg_performance_pct = round(avg_cgpa / 4.0 * 100, 1) if avg_cgpa else 0

    overview_data = {
        "total_students":  total,
        "good_count":      good_count,
        "average_count":   average_count,
        "at_risk_count":   at_risk_count,
        "alerts_count":    len(alerts),
        "average_percent": avg_performance_pct,
        "avg_cgpa":        avg_cgpa,
        "good_percent":    round(good_count    / total * 100, 1) if total else 0,
        "at_risk_percent": round(at_risk_count / total * 100, 1) if total else 0,
    }

    # ══════════════════════════════════════════════════════════════
    #  NEW: Aggregated data for Bento Box dashboard
    # ══════════════════════════════════════════════════════════════

    # ── 1. Class GPA Trend (weekly averages from WeeklyUpdate) ──
    gpa_trend_labels = []
    gpa_trend_values = []
    if student_ids:
        weekly_rows = (
            db.session.query(
                WeeklyUpdate.week_start_date,
                func.avg(StudentProfile.current_cgpa).label("avg_gpa"),
            )
            .join(StudentProfile, WeeklyUpdate.student_id == StudentProfile.id)
            .filter(WeeklyUpdate.student_id.in_(student_ids))
            .group_by(WeeklyUpdate.week_start_date)
            .order_by(WeeklyUpdate.week_start_date)
            .all()
        )
        for row in weekly_rows[-8:]:  # last 8 weeks
            gpa_trend_labels.append(row.week_start_date.strftime("Wk %m/%d") if row.week_start_date else "?")
            gpa_trend_values.append(round(float(row.avg_gpa), 2) if row.avg_gpa else 0)

    # ── 2. Class Skill Breakdown (avg proficiency per skill) ──
    skill_radar_labels = []
    skill_radar_scores = []
    if student_ids:
        skill_rows = (
            db.session.query(
                StudentSkill.skill_name,
                func.avg(StudentSkill.proficiency_score).label("avg_score"),
            )
            .filter(StudentSkill.student_id.in_(student_ids))
            .group_by(StudentSkill.skill_name)
            .order_by(func.count(StudentSkill.student_id).desc())
            .limit(8)
            .all()
        )
        for row in skill_rows:
            skill_radar_labels.append(row.skill_name)
            skill_radar_scores.append(round(float(row.avg_score), 1) if row.avg_score else 0)

    # ── 3. Burnout Risk Overview (with student lists) ──
    burnout_at_risk = 0
    burnout_stable = 0
    burnout_high_achieving = 0
    burnout_students_risk = []
    burnout_students_stable = []
    burnout_students_thriving = []

    # Build a quick id→name map from the already-loaded students list
    student_name_map = {s.id: s.full_name for s in students}

    if student_ids:
        # Get latest WeeklyUpdate per student via subquery
        latest_sub = (
            db.session.query(
                WeeklyUpdate.student_id,
                func.max(WeeklyUpdate.created_at).label("latest")
            )
            .filter(WeeklyUpdate.student_id.in_(student_ids))
            .group_by(WeeklyUpdate.student_id)
            .subquery()
        )
        latest_updates = (
            db.session.query(WeeklyUpdate)
            .join(latest_sub, db.and_(
                WeeklyUpdate.student_id == latest_sub.c.student_id,
                WeeklyUpdate.created_at == latest_sub.c.latest
            ))
            .all()
        )
        for wu in latest_updates:
            score = wu.burnout_risk_score or 0
            entry = {
                "id": wu.student_id,
                "name": student_name_map.get(wu.student_id, "Unknown"),
                "score": round(score * 100),
            }
            if score >= 0.7:
                burnout_at_risk += 1
                burnout_students_risk.append(entry)
            elif score >= 0.3:
                burnout_stable += 1
                burnout_students_stable.append(entry)
            else:
                burnout_high_achieving += 1
                burnout_students_thriving.append(entry)

    # Sort each list by score (highest first for risk, lowest first for thriving)
    burnout_students_risk.sort(key=lambda x: x["score"], reverse=True)
    burnout_students_stable.sort(key=lambda x: x["score"], reverse=True)
    burnout_students_thriving.sort(key=lambda x: x["score"])

    burnout_data = {
        "at_risk": burnout_at_risk,
        "stable": burnout_stable,
        "high_achieving": burnout_high_achieving,
        "at_risk_pct": round(burnout_at_risk / total * 100) if total else 0,
        "stable_pct": round(burnout_stable / total * 100) if total else 0,
        "high_achieving_pct": round(burnout_high_achieving / total * 100) if total else 0,
        "students_risk": burnout_students_risk,
        "students_stable": burnout_students_stable,
        "students_thriving": burnout_students_thriving,
    }

    # ── 4. Career Path Interventions ──
    career_interventions = []
    if student_ids:
        goals_with_career = (
            db.session.query(StudentGoal, CareerPath, StudentProfile, WeeklyUpdate)
            .join(CareerPath, StudentGoal.career_id == CareerPath.id)
            .join(StudentProfile, StudentGoal.student_id == StudentProfile.id)
            .outerjoin(
                WeeklyUpdate,
                db.and_(
                    WeeklyUpdate.student_id == StudentGoal.student_id,
                )
            )
            .filter(
                StudentGoal.student_id.in_(student_ids),
                StudentGoal.is_primary == True,
            )
            .all()
        )
        # Deduplicate: pick latest WeeklyUpdate per student
        student_goal_map = {}
        for goal, career, student, wu in goals_with_career:
            sid = student.id
            if sid not in student_goal_map:
                student_goal_map[sid] = {
                    "student": student,
                    "career": career,
                    "goal": goal,
                    "latest_wu": wu
                }
            else:
                existing_wu = student_goal_map[sid]["latest_wu"]
                if wu and (not existing_wu or wu.created_at > existing_wu.created_at):
                    student_goal_map[sid]["latest_wu"] = wu

        for sid, info in student_goal_map.items():
            wu = info["latest_wu"]
            prob = wu.goal_achievability_prob if wu else None
            # Flag students with low achievability or no data
            if prob is None or prob < 0.5:
                # Find the skill gap reason
                gap_reason = ""
                if info["student"].current_cgpa and info["student"].current_cgpa < 2.5:
                    gap_reason = f"Gap in {info['career'].title} (Low GPA)"
                else:
                    gap_reason = f"{info['career'].title} (Low Achievability)"
                career_interventions.append({
                    "student_name": info["student"].full_name,
                    "career_title": info["career"].title,
                    "gap_reason": gap_reason,
                    "student_id": sid,
                })

    # ── 5. Class Progress to Goals (distribution) ──
    goal_probs = []
    if student_ids:
        # Collect latest goal_achievability_prob per student
        prob_sub = (
            db.session.query(
                WeeklyUpdate.student_id,
                func.max(WeeklyUpdate.created_at).label("latest")
            )
            .filter(WeeklyUpdate.student_id.in_(student_ids))
            .group_by(WeeklyUpdate.student_id)
            .subquery()
        )
        prob_rows = (
            db.session.query(WeeklyUpdate.goal_achievability_prob)
            .join(prob_sub, db.and_(
                WeeklyUpdate.student_id == prob_sub.c.student_id,
                WeeklyUpdate.created_at == prob_sub.c.latest
            ))
            .filter(WeeklyUpdate.goal_achievability_prob != None)
            .all()
        )
        goal_probs = [round(float(r[0]) * 100) for r in prob_rows]

    # Build histogram buckets for bell curve: 0-10, 10-20, ..., 90-100
    goal_buckets = [0] * 10
    for p in goal_probs:
        idx = min(int(p // 10), 9)
        goal_buckets[idx] += 1
    goal_bucket_labels = [f"{i*10}%–{i*10+10}%" for i in range(10)]

    # Class average achievability
    class_avg_prob = round(sum(goal_probs) / len(goal_probs)) if goal_probs else 0

    return render_template(
        "teacher_dashboard.html",
        teacher=teacher,
        overview=overview_data,
        alerts=alerts,
        now_date=datetime.now().strftime("%d %B, %Y"),
        # New bento data
        gpa_trend_labels=gpa_trend_labels,
        gpa_trend_values=gpa_trend_values,
        skill_radar_labels=skill_radar_labels,
        skill_radar_scores=skill_radar_scores,
        burnout=burnout_data,
        career_interventions=career_interventions,
        goal_buckets=goal_buckets,
        goal_bucket_labels=goal_bucket_labels,
        class_avg_prob=class_avg_prob,
        global_transfer_requests=get_global_transfer_requests(teacher),
    )


@teacher_bp.route("/teacher/students")
@jwt_required()
def teacher_students_page():
    teacher, err = _get_teacher_or_403()
    if err:
        return err

    students = (
        StudentProfile.query
        .join(TeacherAssignment, TeacherAssignment.student_id == StudentProfile.id)
        .filter(TeacherAssignment.teacher_id == teacher.id)
        .distinct()
        .all()
    )
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
        "total_students": len(students),
        "alerts_count":   alerts_count,
    }

    from models.teacher import AssignmentTransferRequest
    from sqlalchemy.orm import joinedload
    
    incoming_requests = (
        AssignmentTransferRequest.query
        .options(joinedload(AssignmentTransferRequest.requester), joinedload(AssignmentTransferRequest.student))
        .filter_by(current_owner_id=teacher.id, status="pending")
        .all()
    )

    outgoing_requests = (
        AssignmentTransferRequest.query
        .options(joinedload(AssignmentTransferRequest.current_owner), joinedload(AssignmentTransferRequest.student))
        .filter_by(requester_id=teacher.id, status="pending")
        .all()
    )

    return render_template(
        "teacher_students.html",
        teacher=teacher,
        overview=overview_data,
        students=students,
        incoming_requests=incoming_requests,
        outgoing_requests=outgoing_requests,
        now_date=datetime.now().strftime("%d %B, %Y"),
        global_transfer_requests=get_global_transfer_requests(teacher),
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

    from models.teacher import AssignmentTransferRequest
    from sqlalchemy.orm import joinedload
    
    incoming_requests = (
        AssignmentTransferRequest.query
        .options(joinedload(AssignmentTransferRequest.requester), joinedload(AssignmentTransferRequest.student))
        .filter_by(current_owner_id=teacher.id, status="pending")
        .all()
    )

    return render_template(
        "teacher_alerts.html",
        teacher=teacher,
        alerts=alerts,
        incoming_requests=incoming_requests,
        total_alerts=total_alerts_count,
        has_next=has_next,
        next_page=page + 1 if has_next else None,
        now_date=datetime.now().strftime("%d %B, %Y"),
        global_transfer_requests=get_global_transfer_requests(teacher),
    )


@teacher_bp.route("/teacher/student/<int:student_id>")
@jwt_required()
def teacher_student_detail(student_id):
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

    assignment = TeacherAssignment.query.filter_by(
        teacher_id=teacher.id, student_id=student_id
    ).first()
    if not assignment:
        return jsonify({"msg": "You are not assigned to this student"}), 403

    student = StudentProfile.query.get(student_id)
    if not student:
        return jsonify({"msg": "Student not found"}), 404

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

    days_since_active = None
    if student.last_activity:
        days_since_active = (datetime.utcnow() - student.last_activity).days

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

    try:
        predicted_gpa = round(analytics_engine.predict_next_gpa(student_id), 2)
    except Exception:
        predicted_gpa = None

    academic_snapshot = {
        "predicted_next_gpa": predicted_gpa,
        "total_credits":      total_credits,
        "semester_trend":     semester_gpa_trend[-3:],
    }

    # C) Skill snapshot — top 3 by highest risk_score
    top_risk_skills = (
        StudentSkill.query
        .filter_by(student_id=student_id)
        .order_by(StudentSkill.risk_score.desc())
        .limit(3)
        .all()
    )
    skill_snapshot = [
        {
            "skill_name":        s.skill_name,
            "proficiency_score": s.proficiency_score,
            "risk_score":        round(s.risk_score * 100) if s.risk_score else 0,
        }
        for s in top_risk_skills
    ]

    # D) Weekly snapshot
    latest_update = (
        WeeklyUpdate.query
        .filter_by(student_id=student_id)
        .order_by(WeeklyUpdate.created_at.desc())
        .first()
    )
    weekly_snapshot = None
    if latest_update:
        weekly_snapshot = {
            "total_hours_studied":    latest_update.total_hours_studied or 0,
            "burnout_risk_pct":       int((latest_update.burnout_risk_score or 0) * 100),
            "goal_achievability_pct": int((latest_update.goal_achievability_prob or 0) * 100),
            "status_label":           latest_update.status_label or "N/A",
        }

    # E) Career snapshot
    primary_goal = StudentGoal.query.filter_by(student_id=student_id, is_primary=True).first()
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

    # G) Full Dashboard Data (for rendering interactive charts)
    # NOTE: get_dashboard_data() resolves via StudentProfile.user_id,
    # so we must pass the student's user_id, NOT the StudentProfile.id.
    dashboard_data = DashboardService.get_dashboard_data(student.user_id)

    return render_template(
        "student_detail.html",
        teacher=teacher,
        student=student,
        data=dashboard_data,
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
        global_transfer_requests=get_global_transfer_requests(teacher),
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

    students = query.distinct().all()
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
    return jsonify(result)




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

    # Subquery to exclude students assigned to the current teacher
    assigned_to_me = (
        db.session.query(TeacherAssignment.student_id)
        .filter_by(teacher_id=teacher.id)
        .subquery()
    )

    rows = (
        db.session.query(StudentProfile, TeacherProfile.full_name)
        .outerjoin(TeacherAssignment, TeacherAssignment.student_id == StudentProfile.id)
        .outerjoin(TeacherProfile, TeacherAssignment.teacher_id == TeacherProfile.id)
        .filter(StudentProfile.id.notin_(assigned_to_me))
        .order_by(StudentProfile.full_name)
        .all()
    )

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
            "assigned_teacher":   t_name,
        }
        for s, t_name in rows
    ])


@teacher_bp.route("/api/teacher/assign-student", methods=["POST"])
@jwt_required()
def api_assign_student():
    """Create a TeacherAssignment row linking this teacher to a student."""
    teacher, err = _get_teacher_or_403()
    if err:
        return err

    data       = request.get_json(silent=True) or {}
    student_id = data.get("student_id")
    if not student_id:
        return jsonify({"msg": "student_id is required"}), 400

    student = StudentProfile.query.get(int(student_id))
    if not student:
        return jsonify({"msg": "Student not found"}), 404

    existing_assignment = TeacherAssignment.query.filter_by(
        student_id=student.id
    ).first()
    if existing_assignment:
        if existing_assignment.teacher_id == teacher.id:
            return jsonify({"msg": "Student is already assigned to you"}), 409
        else:
            return jsonify({"msg": "Student is already assigned to another teacher and needs to be unassigned inorder to be assigned."}), 409

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
def api_unassign_student():
    """Remove a TeacherAssignment row for the current teacher."""
    teacher, err = _get_teacher_or_403()
    if err:
        return err

    data       = request.get_json(silent=True) or {}
    student_id = data.get("student_id")
    if not student_id:
        return jsonify({"msg": "student_id is required"}), 400

    assignment = TeacherAssignment.query.filter_by(
        teacher_id=teacher.id, student_id=int(student_id)
    ).first()
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    db.session.delete(assignment)
    db.session.commit()
    return jsonify({"success": True})

from models.teacher import AssignmentTransferRequest

@teacher_bp.route("/api/teacher/request-assignment", methods=["POST"])
@jwt_required()
def api_request_assignment():
    teacher, err = _get_teacher_or_403()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    student_id = data.get("student_id")
    if not student_id:
        return jsonify({"msg": "student_id is required"}), 400

    student = StudentProfile.query.get(int(student_id))
    if not student:
        return jsonify({"msg": "Student not found"}), 404

    existing_assignment = TeacherAssignment.query.filter_by(student_id=student.id).first()
    if not existing_assignment:
        return jsonify({"msg": "Student is currently unassigned; please assign directly."}), 400
    
    if existing_assignment.teacher_id == teacher.id:
        return jsonify({"msg": "Student is already assigned to you!"}), 400

    existing_request = AssignmentTransferRequest.query.filter_by(
        requester_id=teacher.id,
        student_id=student.id,
        status="pending"
    ).first()

    if existing_request:
        return jsonify({"msg": "You already have a pending request for this student."}), 409

    current_owner = TeacherProfile.query.get(existing_assignment.teacher_id)

    transfer_req = AssignmentTransferRequest(
        requester_id=teacher.id,
        current_owner_id=existing_assignment.teacher_id,
        student_id=student.id
    )
    db.session.add(transfer_req)
    db.session.commit()

    return jsonify({
        "success": True,
        "request_id": transfer_req.id,
        "student_name": student.full_name,
        "current_owner_name": current_owner.full_name if current_owner else "Unknown",
    })

@teacher_bp.route("/api/teacher/resolve-request", methods=["POST"])
@jwt_required()
def api_resolve_transfer_request():
    teacher, err = _get_teacher_or_403()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    request_id = data.get("request_id")
    action = data.get("action")

    if not request_id or action not in ["accept", "reject", "cancel"]:
        return jsonify({"msg": "Invalid payload."}), 400

    transfer_req = AssignmentTransferRequest.query.get(int(request_id))
    if not transfer_req:
        return jsonify({"msg": "Request not found"}), 404

    if action in ["accept", "reject"] and transfer_req.current_owner_id != teacher.id:
        return jsonify({"msg": "Unauthorized"}), 403

    if action == "cancel" and transfer_req.requester_id != teacher.id:
        return jsonify({"msg": "Unauthorized"}), 403

    if transfer_req.status != "pending":
        return jsonify({"msg": "Request is already resolved"}), 400

    if action == "accept":
        existing_assignment = TeacherAssignment.query.filter_by(student_id=transfer_req.student_id, teacher_id=teacher.id).first()
        if existing_assignment:
            db.session.delete(existing_assignment)
        
        new_assignment = TeacherAssignment(
            teacher_id=transfer_req.requester_id,
            student_id=transfer_req.student_id,
            assignment_type="homeroom"
        )
        db.session.add(new_assignment)
        transfer_req.status = "accepted"
    elif action == "reject":
        transfer_req.status = "rejected"
    elif action == "cancel":
        db.session.delete(transfer_req)

    db.session.commit()
    return jsonify({"success": True})

# ─────────────────────────────────────────────────────────────────────────────
# TEACHER NOTES — Page + APIs
# ─────────────────────────────────────────────────────────────────────────────

@teacher_bp.route("/teacher/notes")
@jwt_required()
def teacher_notes_page():
    """Render the My Notes read-only history page."""
    teacher, err = _get_teacher_or_403()
    if err:
        return err
    return render_template(
        "teacher_notes.html",
        teacher=teacher,
        now_date=datetime.now().strftime("%d %B, %Y"),
        global_transfer_requests=get_global_transfer_requests(teacher),
    )


@teacher_bp.route("/api/teacher/notes", methods=["GET"])
@jwt_required()
def api_get_teacher_notes():
    """Return all notes created by the current teacher, newest first."""
    teacher, err = _get_teacher_or_403()
    if err:
        return err

    notes = (
        StudentNote.query
        .filter_by(teacher_id=teacher.id)
        .order_by(StudentNote.created_at.desc())
        .all()
    )

    return jsonify([
        {
            "id": n.id,
            "student_name": n.student.full_name if n.student else "Unknown",
            "student_id": n.student_id,
            "content": n.content,
            "is_private": n.is_private,
            "created_at": n.created_at.strftime("%Y-%m-%d %H:%M"),
            "created_at_display": n.created_at.strftime("%b %d, %Y"),
        }
        for n in notes
    ])


@teacher_bp.route("/api/teacher/notes", methods=["POST"])
@jwt_required()
def api_create_note():
    teacher, err = _get_teacher_or_403()
    if err:
        return err

    body       = request.get_json(silent=True) or {}
    student_id = body.get("student_id")
    content    = (body.get("content") or "").strip()

    if not student_id or not content:
        return jsonify({"msg": "student_id and content are required"}), 400

    assigned = TeacherAssignment.query.filter_by(
        teacher_id=teacher.id, student_id=int(student_id)
    ).first()
    if not assigned:
        return jsonify({"msg": "Student not in your assignment scope"}), 403

    note = StudentNote(
        student_id=int(student_id), teacher_id=teacher.id,
        content=content, is_private=False, is_read=False,
    )
    db.session.add(note)
    db.session.commit()
    return jsonify({"success": True, "msg": "Note created", "id": note.id})


# ─────────────────────────────────────────────────────────────────────────────
# TEACHER PROFILE — Page + APIs
# ─────────────────────────────────────────────────────────────────────────────

_ALLOWED_EXTS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def _allowed_pic(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in _ALLOWED_EXTS


@teacher_bp.route("/teacher/profile")
@jwt_required()
def teacher_profile_page():
    """Render the teacher profile page."""
    teacher, err = _get_teacher_or_403()
    if err:
        return err
    return render_template(
        "teacher_profile.html",
        teacher=teacher,
        now_date=datetime.now().strftime("%d %B, %Y"),
        global_transfer_requests=get_global_transfer_requests(teacher),
    )


@teacher_bp.route("/api/teacher/profile", methods=["POST"])
@jwt_required()
def api_update_teacher_profile():
    """Update teacher profile text fields."""
    teacher, err = _get_teacher_or_403()
    if err:
        return err

    body = request.get_json(silent=True) or {}
    fields = [
        "full_name", "designation", "department", "faculty",
        "subject_specialization", "personal_webpage",
        "email", "phone", "cell_phone",
    ]
    for f in fields:
        if f in body:
            val = (body[f] or "").strip()
            setattr(teacher, f, val or None)

    db.session.commit()
    return jsonify({"success": True, "msg": "Profile updated"})


@teacher_bp.route("/api/teacher/profile/picture", methods=["POST"])
@jwt_required()
def api_update_teacher_picture():
    """Upload and save teacher profile picture."""
    teacher, err = _get_teacher_or_403()
    if err:
        return err

    if 'picture' not in request.files:
        return jsonify({"success": False, "msg": "No file provided"}), 400

    file = request.files['picture']
    if not file.filename or not _allowed_pic(file.filename):
        return jsonify({"success": False, "msg": "Invalid file type"}), 400

    # Build upload directory
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'teacher_pics')
    os.makedirs(upload_dir, exist_ok=True)

    # Remove old picture if present
    if teacher.profile_picture:
        old_path = os.path.join(upload_dir, teacher.profile_picture)
        if os.path.exists(old_path):
            os.remove(old_path)

    ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()
    filename = f"teacher_{teacher.id}_{uuid.uuid4().hex[:8]}.{ext}"
    file.save(os.path.join(upload_dir, filename))

    teacher.profile_picture = filename
    db.session.commit()
    return jsonify({"success": True, "filename": filename, "msg": "Picture updated"})


@teacher_bp.route("/api/teacher/profile/delete", methods=["DELETE"])
@jwt_required()
def api_delete_teacher_profile():
    """Delete the teacher profile, free all assigned students, and remove the user account."""
    teacher, err = _get_teacher_or_403()
    if err:
        return err

    try:
        user_id = teacher.user_id

        # 1. Delete all assignments (frees students)
        TeacherAssignment.query.filter_by(teacher_id=teacher.id).delete()

        # 2. Cancel all pending transfer requests (both incoming and outgoing)
        AssignmentTransferRequest.query.filter(
            db.or_(
                AssignmentTransferRequest.requester_id == teacher.id,
                AssignmentTransferRequest.current_owner_id == teacher.id,
            )
        ).delete(synchronize_session='fetch')

        # 3. Delete teacher notes
        StudentNote.query.filter_by(teacher_id=teacher.id).delete()

        # 4. Remove profile picture file
        if teacher.profile_picture:
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'teacher_pics')
            pic_path = os.path.join(upload_dir, teacher.profile_picture)
            if os.path.exists(pic_path):
                os.remove(pic_path)

        # 5. Delete the teacher profile
        db.session.delete(teacher)

        # 6. Delete the user account
        from models.user import User
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)

        db.session.commit()
        return jsonify({"success": True, "msg": "Profile deleted successfully."})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Profile deletion failed: {e}")
        return jsonify({"success": False, "msg": "Failed to delete profile."}), 500

