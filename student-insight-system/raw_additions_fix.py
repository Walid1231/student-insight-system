++ b/student-insight-system/dashboard/teacher_routes.py
from sqlalchemy.orm import selectinload, joinedload
from core.extensions import cache
    page = request.args.get('page', 1, type=int)

    students_query = (
    
    pagination = students_query.paginate(page=page, per_page=25, error_out=False)
    students = pagination.items

        "total_students": pagination.total,
        pagination=pagination,
    # Get page number from request args, default to 1
    page = request.args.get("page", 1, type=int)

    alerts_pagination = None
        alerts_pagination = (
            .paginate(page=page, per_page=20, error_out=False)
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

        total_alerts=total_alerts_count,
        has_next=has_next,
        next_page=page + 1 if has_next else None,
        return jsonify({"success": False, "msg": "Access denied"}), 403
        return jsonify({"success": False, "msg": "Invalid user identity"}), 400
        return jsonify({"success": False, "msg": "Teacher profile not found"}), 404
        return jsonify({"success": False, "msg": "You are not assigned to this student"}), 403

    student = StudentProfile.query.options(
        joinedload(StudentProfile.skills),
        joinedload(StudentProfile.student_goals),
        joinedload(StudentProfile.weekly_updates)
    ).get(student_id)
    
        return jsonify({"success": False, "msg": "Student not found"}), 404
    # Cached AI Prediction
    @cache.memoize(timeout=600)
    def get_predicted_gpa(sid):
        try:
            return round(analytics_engine.predict_next_gpa(sid), 2)
        except Exception:
            return None

    predicted_gpa = get_predicted_gpa(student_id)
    # C) Skill snapshot
    top_risk_skills = sorted(student.skills, key=lambda s: s.risk_score or 0, reverse=True)[:3]
    latest_update = sorted(student.weekly_updates, key=lambda w: w.created_at, reverse=True)
    latest_update = latest_update[0] if latest_update else None
    
    primary_goal = next((g for g in student.student_goals if g.is_primary), None)
    pagination = query.distinct().paginate(page=request.args.get('page', 1, type=int), per_page=25, error_out=False)
    students = pagination.items
    return jsonify({"success": True, "students": result, "total": pagination.total})
def api_teacher_add_note():
        return jsonify({"success": False, "msg": "student_id and content are required"}), 400
        return jsonify({"success": False, "msg": "Student not in your assignment scope"}), 403
    
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
    # Require application/json content type for security against CSRF
    if not request.is_json:
        return jsonify({"success": False, "msg": "Content-Type must be application/json"}), 400

        return jsonify({"success": False, "msg": "Alert not found or not in your scope"}), 404
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
    search_query = (request.args.get("search") or "").strip()

    
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
def api_teacher_assign_student():
        return jsonify({"success": False, "msg": "student_id is required"}), 400

    # Enforce max 50 students
    current_count = TeacherAssignment.query.filter_by(teacher_id=teacher.id).count()
    if current_count >= 50:
        return jsonify({"success": False, "msg": "Assignment limit of 50 students exceeded"}), 400
        return jsonify({"success": False, "msg": "Student not found"}), 404
        return jsonify({"success": False, "msg": "Student is already assigned to you"}), 409
def api_teacher_unassign_student():
        return jsonify({"success": False, "msg": "student_id is required"}), 400
        return jsonify({"success": False, "msg": "Assignment not found or does not belong to you"}), 403
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
