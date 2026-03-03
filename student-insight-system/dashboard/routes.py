"""
dashboard/routes.py — Thin controllers for student-facing routes.

All business logic has been extracted into the services/ package.
Each handler: validates input → calls service → returns response.
"""

import os
from flask import (
    Blueprint, render_template, jsonify, request,
    redirect, url_for, current_app,
)
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from core.security import require_role
from core.errors import NotFoundError

from services.dashboard_service import DashboardService
from services.session_service import SessionService
from services.academic_service import AcademicService
from services.skill_service import SkillService
from services.checkin_service import CheckinService
from services.profile_service import ProfileService
from services.analytics_service import AnalyticsService

dashboard_bp = Blueprint("dashboard", __name__)


# =============================================================
# STUDENT DASHBOARD
# =============================================================

@dashboard_bp.route("/student/dashboard")
@require_role("student")
def student_dashboard():
    user_id = get_jwt_identity()
    data = DashboardService.get_dashboard_data(user_id)

    if data.pop("_is_new_student", False):
        return redirect(url_for('dashboard.onboarding_checklist'))

    return render_template("student_analytics.html", data=data)


# =============================================================
# STUDENT ONBOARDING
# =============================================================

@dashboard_bp.route("/student/onboarding")
@require_role("student")
def onboarding_checklist():
    user_id = get_jwt_identity()
    data = DashboardService.get_onboarding_data(user_id)

    if data["all_complete"]:
        return redirect(url_for('dashboard.student_dashboard'))

    return render_template("student_onboarding.html", data=data)


# =============================================================
# CV / PROFILE CREATION
# =============================================================

@dashboard_bp.route("/create-profile", methods=["GET", "POST"])
@require_role("student")
def create_profile():
    if request.method == "POST":
        # Handle optional photo upload
        photo_filename = None
        if 'photo' in request.files:
            from werkzeug.utils import secure_filename
            file = request.files['photo']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                upload_folder = os.path.join(request.root_path, '..', 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, filename))
                photo_filename = filename

        cv_data = ProfileService.build_cv_data(request.form)
        cv_data["photo"] = photo_filename
        return render_template("cv_classic.html", cv=cv_data)

    return render_template("create_profile.html")


# =============================================================
# AI INSIGHT REPORT
# =============================================================

@dashboard_bp.route("/student/insight-report", methods=["GET", "POST"])
@require_role("student")
def student_insight_report():
    if request.method == "POST":
        user_id = get_jwt_identity()

        # Get AI service from app config or create one
        ai_service = current_app.config.get("AI_SERVICE")
        if not ai_service:
            from infrastructure.ai.gemini_service import GeminiAIService
            api_key = current_app.config.get("GEMINI_API_KEY")
            ai_service = GeminiAIService(api_key)

        report_html = AnalyticsService.generate_insight_report(
            user_id, dict(request.form), ai_service
        )
        return jsonify({"success": True, "report": report_html})

    return render_template("student_insight_form.html")


# =============================================================
# SKILL TRACKING & ACTION PLAN API
# =============================================================

@dashboard_bp.route("/api/skills/update", methods=["POST"])
@require_role("student")
def api_update_skill():
    user_id = get_jwt_identity()
    data = request.get_json()
    skill_name = data.get('skill_name')
    proficiency = int(data.get('proficiency', 0))

    if not skill_name:
        return jsonify({"msg": "Skill name required"}), 400

    result = SkillService.update_skill(user_id, skill_name, proficiency)
    return jsonify({"msg": "Skill updated", **result})


@dashboard_bp.route("/api/skills/history", methods=["GET"])
@require_role("student")
def api_get_skill_history():
    user_id = get_jwt_identity()
    data = SkillService.get_skill_history(user_id)
    return jsonify(data)


@dashboard_bp.route("/api/action-plans", methods=["GET"])
@require_role("student")
def api_get_action_plans():
    user_id = get_jwt_identity()
    plans = SkillService.get_action_plans(user_id)
    return jsonify(plans)


@dashboard_bp.route("/api/action-plans/generate", methods=["POST"])
@require_role("student")
def api_generate_action_plan():
    user_id = get_jwt_identity()

    ai_service = current_app.config.get("AI_SERVICE")
    if not ai_service:
        from infrastructure.ai.gemini_service import GeminiAIService
        api_key = current_app.config.get("GEMINI_API_KEY")
        if not api_key:
            return jsonify({"success": False, "msg": "GEMINI_API_KEY not configured"}), 500
        ai_service = GeminiAIService(api_key)

    result = SkillService.generate_action_plan(user_id, ai_service)
    return jsonify(result)


@dashboard_bp.route("/api/action-plans/<int:plan_id>/complete", methods=["POST"])
@require_role("student")
def api_complete_action_plan(plan_id):
    user_id = get_jwt_identity()
    result = SkillService.complete_action_plan(user_id, plan_id)
    return jsonify({"msg": "Plan completed", "new_score": result["new_score"]})


# =============================================================
# PROFILE & SETTINGS
# =============================================================

@dashboard_bp.route("/student/profile", methods=["GET", "POST"])
@require_role("student")
def student_profile():
    user_id = get_jwt_identity()

    if request.method == "POST":
        from schemas.student import ProfileUpdate
        try:
            data = ProfileUpdate(
                full_name=request.form.get("full_name", ""),
                university=request.form.get("university"),
                department=request.form.get("department"),
                current_year=request.form.get("current_year"),
                cgpa=request.form.get("cgpa") or None,
                career_goal=request.form.get("career_goal"),
                linkedin_profile=request.form.get("linkedin_profile"),
                github_profile=request.form.get("github_profile"),
                bio=request.form.get("bio"),
            )
        except Exception:
            return redirect(url_for('dashboard.student_profile'))

        ProfileService.update_profile(
            user_id, data,
            profile_picture_file=request.files.get('profile_picture'),
            upload_root=current_app.root_path,
        )
        return redirect(url_for('dashboard.student_profile'))

    student = ProfileService.get_profile(user_id)
    return render_template("student_profile.html", student=student)


@dashboard_bp.route("/student/delete-profile", methods=["DELETE"])
@require_role("student")
def delete_profile():
    user_id = get_jwt_identity()
    ProfileService.delete_profile(user_id)
    return jsonify({"success": True})


@dashboard_bp.route("/student/update-data", methods=["GET"])
@require_role("student")
def view_update_data():
    return render_template("update_profile_data.html")


@dashboard_bp.route("/update-progress", methods=["POST"])
@require_role("student")
def update_progress():
    from models import CareerInterest, StudentSkill
    from core.extensions import db

    user_id = get_jwt_identity()
    student = ProfileService.get_profile(user_id)

    student.university = request.form.get("university")
    student.department = request.form.get("department")
    try:
        student.current_cgpa = float(request.form.get("current_cgpa"))
    except (ValueError, TypeError):
        pass

    CareerInterest.query.filter_by(student_id=student.id).delete()
    role1 = request.form.get("role_1")
    match1 = request.form.get("match_1")
    if role1:
        db.session.add(CareerInterest(
            student_id=student.id, field_name=role1,
            interest_score=float(match1) if match1 else 0,
        ))
    role2 = request.form.get("role_2")
    match2 = request.form.get("match_2")
    if role2:
        db.session.add(CareerInterest(
            student_id=student.id, field_name=role2,
            interest_score=float(match2) if match2 else 0,
        ))

    skills_known = request.form.get("skills_known", "")
    for skill_name in skills_known.split(','):
        s_name = skill_name.strip()
        if s_name:
            existing = StudentSkill.query.filter_by(
                student_id=student.id, skill_name=s_name
            ).first()
            if not existing:
                db.session.add(StudentSkill(
                    student_id=student.id, skill_name=s_name, proficiency_score=50,
                ))

    db.session.commit()
    return redirect(url_for('dashboard.student_dashboard'))


@dashboard_bp.route("/student/settings", methods=["GET"])
@require_role("student")
def student_settings():
    user_id = get_jwt_identity()
    data = ProfileService.get_settings_data(user_id)
    return render_template("student_settings.html", **data)


# =============================================================
# WEEKLY ROUTINE & STUDY SESSIONS
# =============================================================

@dashboard_bp.route("/student/weekly-routine", methods=["GET"])
@require_role("student")
def student_routine():
    user_id = get_jwt_identity()
    data = SessionService.get_routine_data(user_id)
    return render_template("student_weekly_routine.html", **data)


@dashboard_bp.route("/student/add-study-session", methods=["POST"])
@require_role("student")
def add_study_session():
    from schemas.student import StudySessionCreate
    user_id = get_jwt_identity()

    try:
        payload = StudySessionCreate.from_form(request.form)
    except Exception as e:
        return jsonify({"msg": f"Invalid data: {e}"}), 400

    SessionService.create_session(user_id, payload)
    return redirect(url_for('dashboard.student_routine'))


@dashboard_bp.route("/student/update-study-session/<int:session_id>", methods=["POST"])
@require_role("student")
def update_study_session(session_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    result = SessionService.update_session(user_id, session_id, data)
    return jsonify({"success": True, "session": result})


@dashboard_bp.route("/student/delete-study-session/<int:session_id>", methods=["POST"])
@require_role("student")
def delete_study_session(session_id):
    user_id = get_jwt_identity()
    try:
        SessionService.delete_session(user_id, session_id)
        return jsonify({"success": True})
    except NotFoundError as e:
        return jsonify({"success": False, "error": str(e)}), 404



# =============================================================
# WEEKLY CHECK-IN
# =============================================================

@dashboard_bp.route("/student/weekly-checkin", methods=["GET"])
@require_role("student")
def weekly_checkin():
    user_id = get_jwt_identity()
    data = CheckinService.get_checkin_data(user_id)
    success = request.args.get('success', False)
    return render_template("student_weekly_checkin.html", success=success, **data)


@dashboard_bp.route("/student/weekly-checkin", methods=["POST"])
@require_role("student")
def submit_weekly_checkin():
    from schemas.student import WeeklyCheckinSubmit
    user_id = get_jwt_identity()

    try:
        payload = WeeklyCheckinSubmit.from_form(request.form)
    except Exception:
        return redirect(url_for('dashboard.weekly_checkin'))

    CheckinService.submit_checkin(user_id, payload)
    return redirect(url_for('dashboard.weekly_checkin', success=1))


# =============================================================
# GOALS & GRADES
# =============================================================

@dashboard_bp.route("/student/goals-grades", methods=["GET"])
@require_role("student")
def goals_grades():
    user_id = get_jwt_identity()
    data = AcademicService.get_goals_grades_data(user_id)
    data["success"] = request.args.get('success', False)
    data["success_msg"] = request.args.get('msg', '')
    return render_template("student_goals_grades.html", **data)


@dashboard_bp.route("/student/goals-grades/target-cgpa", methods=["POST"])
@require_role("student")
def save_target_cgpa():
    user_id = get_jwt_identity()
    target = request.form.get("target_cgpa")
    if target:
        AcademicService.save_target_cgpa(user_id, float(target))
    return redirect(url_for('dashboard.goals_grades', success=1, msg='Target CGPA saved!'))


@dashboard_bp.route("/student/goals-grades/skills", methods=["POST"])
@require_role("student")
def save_skills():
    user_id = get_jwt_identity()
    selected_ids = [int(x) for x in request.form.getlist("skill_ids")]
    AcademicService.save_skills(user_id, selected_ids)
    return redirect(url_for('dashboard.goals_grades'))


@dashboard_bp.route("/student/goals-grades/skills/add", methods=["POST"])
@require_role("student")
def add_skill_entry():
    user_id = get_jwt_identity()
    skill_name = request.form.get("skill_name", "").strip()
    if skill_name:
        AcademicService.add_skill(user_id, skill_name)
    return redirect(url_for('dashboard.goals_grades'))


@dashboard_bp.route("/student/goals-grades/skills/<int:skill_id>/delete", methods=["POST"])
@require_role("student")
def remove_skill_entry(skill_id):
    user_id = get_jwt_identity()
    AcademicService.remove_skill(user_id, skill_id)
    return redirect(url_for('dashboard.goals_grades'))


@dashboard_bp.route("/student/goals-grades/goal", methods=["POST"])
@require_role("student")
def add_goal():
    user_id = get_jwt_identity()
    career_id = request.form.get("career_id")
    goal_type = request.form.get("goal_type", "Long Term")

    if not career_id:
        return redirect(url_for('dashboard.goals_grades'))

    AcademicService.add_goal(user_id, int(career_id), goal_type)
    return redirect(url_for('dashboard.goals_grades', success=1, msg='Goal added!'))


@dashboard_bp.route("/student/goals-grades/goal/<int:goal_id>/delete", methods=["POST"])
@require_role("student")
def delete_goal(goal_id):
    user_id = get_jwt_identity()
    AcademicService.delete_goal(user_id, goal_id)
    return redirect(url_for('dashboard.goals_grades'))


@dashboard_bp.route("/student/goals-grades/goal/<int:goal_id>/primary", methods=["POST"])
@require_role("student")
def set_primary_goal(goal_id):
    user_id = get_jwt_identity()
    AcademicService.set_primary_goal(user_id, goal_id)
    return redirect(url_for('dashboard.goals_grades', success=1, msg='Primary goal updated!'))


@dashboard_bp.route("/student/goals-grades/grade", methods=["POST"])
@require_role("student")
def add_grade():
    from schemas.academic import GradeInput
    user_id = get_jwt_identity()

    try:
        data = GradeInput.from_form(request.form)
    except Exception:
        return redirect(url_for('dashboard.goals_grades', success=0,
                                msg='Please fill in all fields correctly.'))

    AcademicService.add_grade(user_id, data)
    return redirect(url_for('dashboard.goals_grades', success=1,
                            msg='Grade added! CGPA updated.'))


@dashboard_bp.route("/student/goals-grades/grade/<int:record_id>/delete", methods=["POST"])
@require_role("student")
def delete_grade(record_id):
    user_id = get_jwt_identity()
    AcademicService.delete_grade(user_id, record_id)
    return redirect(url_for('dashboard.goals_grades'))
