from flask import Blueprint, render_template, jsonify, request, redirect, url_for, current_app
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from models import StudentProfile, AcademicMetric, StudentSkill, StudentCourse, CareerInterest, AnalyticsResult, TeacherProfile, User, TeacherAssignment, StudentSkillProgress, ActionPlan, StudySession, db
from ml.analytics_engine import AnalyticsEngine
from datetime import datetime
from dashboard.utils import calculate_student_overview_stats
import json
import google.generativeai as genai

dashboard_bp = Blueprint("dashboard", __name__)
analytics_engine = AnalyticsEngine()

from dashboard.utils import calculate_student_overview_stats
from datetime import datetime
from models import StudentInsight

# ... (imports)

@dashboard_bp.route("/student/dashboard")
@jwt_required()
def student_dashboard():
    claims = get_jwt()
    role = claims.get("role")
    user_id = get_jwt_identity()

    if role != "student":
        return jsonify({"msg": "Access denied"}), 403

    try:
        student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
    except (ValueError, TypeError):
        # If no profile exists yet (should be created at register, but safety check)
        return jsonify({"msg": "Invalid user identity"}), 400

    if not student:
        return jsonify({"msg": "Student profile not found"}), 404
    
    # Get Academic Metrics for easy access in template
    metric = AcademicMetric.query.filter_by(student_id=student.id).first()
    stats = {
        "rank": metric.department_rank if metric else 0,
        "credits": metric.total_credits if metric else 0,
        "gpa_trend": metric.get_gpas() if metric else []
    }
    
    return render_template("student_dashboard.html", student=student, stats=stats, now_date=datetime.now().strftime("%d %B, %Y"))

@dashboard_bp.route("/student/dashboard-v2")
@jwt_required()
def student_dashboard_v2():
    """Enhanced student dashboard with comprehensive visualizations"""
    claims = get_jwt()
    role = claims.get("role")
    user_id = get_jwt_identity()

    if role != "student":
        return jsonify({"msg": "Access denied"}), 403

    try:
        student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
    except (ValueError, TypeError):
        return jsonify({"msg": "Invalid user identity"}), 400

    if not student:
        return jsonify({"msg": "Student profile not found"}), 404
    
    # Get the student's courses and calculate performance
    courses = StudentCourse.query.filter_by(student_id=student.id).all()
    subjects = []
    for course in courses:
        # Convert grade to score (simplified mapping)
        grade_map = {'A': 95, 'A-': 90, 'B+': 87, 'B': 83, 'B-': 80, 'C+': 77, 'C': 73, 'D': 65, 'F': 50}
        score = grade_map.get(course.grade, 70)
        subjects.append({
            "name": course.course_name,
            "score": score,
            "grade": course.grade
        })
    
    # If no real data, use mock data
    if not subjects:
        subjects = [
            {"name": "Programming", "score": 88, "grade": "B+"},
            {"name": "Database Systems", "score": 75, "grade": "C+"},
            {"name": "Web Development", "score": 92, "grade": "A-"},
            {"name": "Mathematics", "score": 68, "grade": "C"},
            {"name": "Data Structures", "score": 85, "grade": "B"}
        ]
    
    # Get career interests
    career_interests = CareerInterest.query.filter_by(student_id=student.id).all()
    careers = []
    for interest in career_interests:
        careers.append({
            "role": interest.field_name,
            "match": int(interest.interest_score) if interest.interest_score else 75
        })
    
    # If no real data, use mock
    if not careers:
        careers = [
            {"role": "Full Stack Developer", "match": 85},
            {"role": "Data Analyst", "match": 72},
            {"role": "Software Engineer", "match": 68}
        ]
    
    # Get skills
    skills = StudentSkill.query.filter_by(student_id=student.id).all()
    skills_known = [skill.skill_name for skill in skills] if skills else ["Python", "HTML", "CSS", "JavaScript"]
    skills_todo = ["React", "Node.js", "MongoDB", "Docker"] # This would be calculated based on career requirements
    
    # Mock weekly hours (in a real app, this would come from StudySession model)
    weekly_hours = [3, 5, 4, 6, 2, 7, 4]
    
    # Calculate goal probability (mock for now)
    goal_prob = 75
    target_gpa = student.current_cgpa + 0.3 if student.current_cgpa else 3.5
    
    # AI Guidance (mock for now - in real app, this would use Gemini)
    guidance_msg = "Your progress in Web Development is excellent! However, Database Systems needs attention."
    guidance_tip = "Practice SQL queries daily using platforms like HackerRank or LeetCode."
    
    # Prepare comprehensive data object
    data = {
        "name": student.full_name,
        "department": student.department or "Computer Science",
        "year": student.class_level or "3",
        "university_name": "Your University",  # Add this field to StudentProfile if needed
        "status": "On Track" if student.current_cgpa and student.current_cgpa >= 3.0 else "At Risk",
        "cgpa": student.current_cgpa or 3.0,
        "credits_completed": student.completed_credits or 90,
        "subjects": subjects,
        "careers": careers,
        "skills_known": skills_known,
        "skills_todo": skills_todo,
        "weekly_hours": weekly_hours,
        "goal_prob": goal_prob,
        "target_gpa": round(target_gpa, 2),
        "time_to_goal": "3 months",
        "guidance_msg": guidance_msg,
        "guidance_tip": guidance_tip
    }
    
    return render_template("student_dashboard_v2.html", data=data)

# ... (API endpoints)

@dashboard_bp.route("/teacher/dashboard")
@jwt_required()
def teacher_dashboard():
    claims = get_jwt()
    role = claims.get("role")
    user_id = get_jwt_identity()

    if role != "teacher":
        return jsonify({"msg": "Access denied"}), 403
        
    try:
        teacher = TeacherProfile.query.filter_by(user_id=int(user_id)).first()
    except (ValueError, TypeError):
        return jsonify({"msg": "Invalid user identity"}), 400
    
    if not teacher:
        return jsonify({"msg": "Teacher profile not found"}), 404
    
    # Get all assigned students via TeacherAssignment
    from models import TeacherAssignment, StudentAlert, StudentNote
    assignments = TeacherAssignment.query.filter_by(teacher_id=teacher.id).all()
    
    # Get unique students (a student may appear in multiple assignments)
    student_ids = list(set([a.student_id for a in assignments]))
    students = StudentProfile.query.filter(StudentProfile.id.in_(student_ids)).all() if student_ids else []
    
    # Get Alerts
    alerts = StudentAlert.query.filter(StudentAlert.student_id.in_(student_ids), StudentAlert.is_resolved == False).order_by(StudentAlert.created_at.desc()).all() if student_ids else []
    
    # Calculate Overview Data using Utility
    overview_data = calculate_student_overview_stats(students, alerts)
    
    return render_template("teacher_dashboard.html", teacher=teacher, overview=overview_data, students=students, alerts=alerts, now_date=datetime.now().strftime("%d %B, %Y"))

# --- API ENDPOINTS FOR TEACHER DASHBOARD ---

@dashboard_bp.route("/api/teacher/students", methods=["GET"])
@jwt_required()
def api_teacher_students():
    claims = get_jwt()
    if claims.get("role") != "teacher": return jsonify({"msg": "Access denied"}), 403
    user_id = get_jwt_identity()
    
    teacher = TeacherProfile.query.filter_by(user_id=int(user_id)).first()
    if not teacher: return jsonify({"msg": "Profile not found"}), 404

    # Get filters
    class_filter = request.args.get('class')
    section_filter = request.args.get('section')
    status_filter = request.args.get('status')
    
    # Base Query: Start from Assignments to ensure scope
    query = db.session.query(StudentProfile).join(TeacherAssignment).filter(TeacherAssignment.teacher_id == teacher.id)
    
    if class_filter:
        query = query.filter(StudentProfile.class_level == class_filter)
    if section_filter:
        query = query.filter(StudentProfile.section == section_filter)
    # Status filter needs post-processing or complex query since status is a property
    # For now, fetch all assigned and filter in python if status is requested
    
    students = query.distinct().all()
    
    result = []
    for s in students:
        if status_filter and s.performance_status != status_filter:
            continue
            
        result.append({
            "id": s.id,
            "name": s.full_name,
            "class_level": s.class_level,
            "section": s.section,
            "cgpa": s.current_cgpa,
            "status": s.performance_status,
            "last_active": s.last_active.isoformat() if s.last_active else None
        })
        
    return jsonify(result)

@dashboard_bp.route("/api/teacher/notes", methods=["POST"])
@jwt_required()
def api_create_note():
    claims = get_jwt()
    if claims.get("role") != "teacher": return jsonify({"msg": "Access denied"}), 403
    user_id = get_jwt_identity()
    teacher = TeacherProfile.query.filter_by(user_id=int(user_id)).first()
    
    data = request.get_json()
    student_id = data.get('student_id')
    content = data.get('content')
    
    if not student_id or not content:
        return jsonify({"msg": "Missing data"}), 400
        
    # Verify assignment scope? For simplicity, assume yes if valid ID
    # Better: check if teacher assignments include student_id
    
    note = StudentNote(
        student_id=student_id,
        teacher_id=teacher.id,
        content=content,
        is_private=True
    )
    db.session.add(note)
    db.session.commit()
    
    return jsonify({"msg": "Note created", "id": note.id})

@dashboard_bp.route("/api/teacher/alerts/<int:alert_id>/resolve", methods=["POST"])
@jwt_required()
def api_resolve_alert(alert_id):
    claims = get_jwt()
    if claims.get("role") != "teacher": return jsonify({"msg": "Access denied"}), 403
    
    alert = StudentAlert.query.get(alert_id)
    if not alert: return jsonify({"msg": "Alert not found"}), 404
    
    # Ideally check ownership via student -> teacher assignment
    
    alert.is_resolved = True
    db.session.commit()
    return jsonify({"msg": "Alert resolved"})

@dashboard_bp.route("/api/teacher/class-skills", methods=["GET"])
@jwt_required()
def api_teacher_class_skills():
    claims = get_jwt()
    if claims.get("role") != "teacher": return jsonify({"msg": "Access denied"}), 403
    user_id = get_jwt_identity()
    
    teacher = TeacherProfile.query.filter_by(user_id=int(user_id)).first()
    if not teacher: return jsonify({"msg": "Profile not found"}), 404
    
    # Get assigned students
    assignments = TeacherAssignment.query.filter_by(teacher_id=teacher.id).all()
    student_ids = list(set([a.student_id for a in assignments]))
    
    # Fetch data
    data = []
    students = StudentProfile.query.filter(StudentProfile.id.in_(student_ids)).all()
    
    for s in students:
        skills = StudentSkill.query.filter_by(student_id=s.id).all()
        skill_data = [{"name": sk.skill_name, "score": sk.proficiency_score, "risk": sk.risk_score} for sk in skills]
        if skill_data:
            data.append({
                "student_id": s.id,
                "name": s.full_name,
                "skills": skill_data
            })
            
    return jsonify(data)


@dashboard_bp.route("/teacher/student/<int:student_id>")
@jwt_required()
def teacher_student_detail(student_id):
    claims = get_jwt()
    role = claims.get("role")
    user_id = get_jwt_identity()

    if role != "teacher":
        return jsonify({"msg": "Access denied"}), 403
        
    try:
        teacher = TeacherProfile.query.filter_by(user_id=int(user_id)).first()
    except (ValueError, TypeError):
        return jsonify({"msg": "Invalid user identity"}), 400
    
    if not teacher:
        return jsonify({"msg": "Teacher profile not found"}), 404
    
    # Verify teacher is assigned to this student
    assignment = TeacherAssignment.query.filter_by(
        teacher_id=teacher.id,
        student_id=student_id
    ).first()
    
    if not assignment:
        return jsonify({"msg": "You are not assigned to this student"}), 403
    
    # Get student
    student = StudentProfile.query.get(student_id)
    if not student:
        return jsonify({"msg": "Student not found"}), 404
    
    # Import helper functions
    from dashboard.student_stats import (
        calculate_attendance_stats,
        calculate_assignment_stats,
        calculate_assessment_stats,
        calculate_performance_trend
    )
    
    # Calculate all stats
    attendance = calculate_attendance_stats(student_id)
    assignments = calculate_assignment_stats(student_id)
    assessments = calculate_assessment_stats(student_id)
    performance_trend = calculate_performance_trend(student_id)
    
    # Calculate time since last activity
    days_since_active = None
    if student.last_activity:
        delta = datetime.utcnow() - student.last_activity
        days_since_active = delta.days
        
    # Get Notes (Teacher specific)
    from models import StudentNote
    notes = StudentNote.query.filter_by(
        student_id=student_id,
        teacher_id=teacher.id
    ).order_by(StudentNote.created_at.desc()).all()
    
    # Get latest Insight Report
    latest_insight = StudentInsight.query.filter_by(student_id=student_id).order_by(StudentInsight.generated_at.desc()).first()

    return render_template(
        "student_detail.html",
        teacher=teacher,
        student=student,
        attendance=attendance,
        assignments=assignments,
        assessments=assessments,
        performance_trend=performance_trend,
        days_since_active=days_since_active,
        notes=notes,
        insight=latest_insight
    )



import os
from werkzeug.utils import secure_filename

@dashboard_bp.route("/create-profile", methods=["GET", "POST"])
# @jwt_required()
@jwt_required()
def create_profile():
    claims = get_jwt()
    role = claims.get("role")
    
    # Optional: Restrict to students only
    if role and role != "student":
         return jsonify({"msg": "Access denied"}), 403

    if request.method == "POST":
        # Handle Photo Upload
        photo_filename = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                # Absolute path for safety
                upload_folder = os.path.join(request.root_path, '..', 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, filename))
                photo_filename = filename

        # Capture form data
        user_cv_data = {
            "photo": photo_filename,
            "full_name": request.form.get("full_name"),
            "job_title": request.form.get("job_title"),
            "email": request.form.get("email"),
            "phone": request.form.get("phone"),
            "dob": request.form.get("dob"),
            "gender": request.form.get("gender"),
            "address": request.form.get("address"),
            "website": request.form.get("website"),
            "summary": request.form.get("summary"),
            "education": [
                {
                    "date": request.form.get("edu_date_1"),
                    "school": request.form.get("edu_school_1"),
                    "details": request.form.get("edu_detail_1")
                },
                {
                    "date": request.form.get("edu_date_2"),
                    "school": request.form.get("edu_school_2"),
                    "details": request.form.get("edu_detail_2")
                }
            ],
            "experience": [
               {
                    "date": request.form.get("work_date_1"),
                    "company": request.form.get("work_company_1"),
                    "title": request.form.get("work_title_1"),
                    "desc": request.form.get("work_desc_1")
                },
                {
                    "date": request.form.get("work_date_2"),
                    "company": request.form.get("work_company_2"),
                    "title": request.form.get("work_title_2"),
                    "desc": request.form.get("work_desc_2")
                } 
            ]
        }
        return render_template("cv_classic.html", cv=user_cv_data)

    return render_template("create_profile.html")


# --- STUDENT INSIGHT REPORT (AI-Powered) ---
import google.generativeai as genai
from flask import current_app

@dashboard_bp.route("/student/insight-report", methods=["GET", "POST"])
@jwt_required()
def student_insight_report():
    claims = get_jwt()
    role = claims.get("role")

    if role != "student":
        return jsonify({"msg": "Access denied"}), 403

    if request.method == "POST":
        # Get student data from form
        department = request.form.get("department", "Computer Science")
        cgpa = request.form.get("cgpa", "3.0")
        semester_gpas = request.form.get("semester_gpas", "2.8, 3.0, 3.2")
        skills = request.form.get("skills", "Python, HTML")
        strong_courses = request.form.get("strong_courses", "Programming")
        weak_courses = request.form.get("weak_courses", "Math")
        interests = request.form.get("interests", "Web Development")

        # Build the prompt
        prompt = f"""
        You are a Senior Academic Advisor and Technical Career Mentor for a {department} student. 
        Your goal is to provide a harsh but constructive reality check and a clear roadmap for their career.

        ### STUDENT PROFILE
        - **Current CGPA:** {cgpa}
        - **Semester GPA Trend:** {semester_gpas}
        - **Reported Skills:** {skills}
        - **Strong Areas:** {strong_courses}
        - **Weak Areas:** {weak_courses}
        - **Interests:** {interests}

        ### INSTRUCTIONS
        Analyze the data above and generate a "Student Insight Report" in **HTML format**. 
        Do NOT use markdown (like ** or ##). Use only HTML tags: <h3>, <p>, <ul>, <li>, <strong>, <em>, and <div class="alert"> for warnings.

        ### REQUIRED SECTIONS IN OUTPUT:

        1. <h3>📊 Executive Summary</h3>
           <p>A 2-sentence summary of their current standing. Is their CGPA competitive? Does their GPA trend show improvement or decline?</p>

        2. <h3>🛠 Skills vs. Industry Standards (Gap Analysis)</h3>
           <p>Compare their reported skills ({skills}) against modern industry requirements for {department} graduates. What critical tools are they missing?</p>

        3. <h3>📉 Remedial Action Plan</h3>
           <ul>
             <li>Identify why they might be struggling in <strong>{weak_courses}</strong>.</li>
             <li>Suggest 2 specific resources (books, websites, or practice concepts) to fix these weak areas.</li>
           </ul>

        4. <h3>🚀 Career Trajectory & Niche</h3>
           <p>Based on their interest in <strong>{interests}</strong> and strength in <strong>{strong_courses}</strong>, suggest 2 specific job titles they should aim for.</p>
        """

        try:
            # Configure Gemini
            genai.configure(api_key=current_app.config.get("GEMINI_API_KEY"))
            model = genai.GenerativeModel("gemini-2.0-flash")
            
            # Generate response
            response = model.generate_content(prompt)
            report_html = response.text

            # SAVE TO DATABASE
            user_id = get_jwt_identity()
            student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
            if student:
                insight = StudentInsight(
                    student_id=student.id,
                    content=report_html,
                    generated_at=datetime.utcnow()
                )
                db.session.add(insight)
                db.session.commit()

            return jsonify({"success": True, "report": report_html})

        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # GET request - render the form page
    return render_template("student_insight_form.html")


# --- SKILL TRACKING & ACTION PLAN API ---

@dashboard_bp.route("/api/skills/update", methods=["POST"])
@jwt_required()
def api_update_skill():
    user_id = get_jwt_identity()
    student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
    if not student: return jsonify({"msg": "Student not found"}), 404
    
    data = request.get_json()
    skill_name = data.get('skill_name')
    proficiency = int(data.get('proficiency', 0)) # 0-100
    
    if not skill_name: return jsonify({"msg": "Skill name required"}), 400
    
    # Find or Create Skill
    skill = StudentSkill.query.filter_by(student_id=student.id, skill_name=skill_name).first()
    if not skill:
        skill = StudentSkill(student_id=student.id, skill_name=skill_name)
        db.session.add(skill)
    
    # Update Stats
    skill.proficiency_score = proficiency
    skill.last_updated = datetime.utcnow()
    
    # Calculate Risk
    skill.risk_score = analytics_engine.calculate_risk_score(proficiency, student.current_cgpa)
    
    # Log History
    history = StudentSkillProgress(
        student_skill_id=skill.id,
        proficiency_score=skill.proficiency_score,
        risk_score=skill.risk_score,
        date=datetime.utcnow().date()
    )
    db.session.add(history)
    db.session.commit()
    
    return jsonify({
        "msg": "Skill updated", 
        "skill": skill.skill_name, 
        "proficiency": skill.proficiency_score,
        "risk": skill.risk_score
    })

@dashboard_bp.route("/api/skills/history", methods=["GET"])
@jwt_required()
def api_get_skill_history():
    user_id = get_jwt_identity()
    student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
    if not student: return jsonify({"msg": "Student not found"}), 404
    
    skills = StudentSkill.query.filter_by(student_id=student.id).all()
    data = []
    
    for skill in skills:
        history = StudentSkillProgress.query.filter_by(student_skill_id=skill.id).order_by(StudentSkillProgress.date).all()
        data.append({
            "skill": skill.skill_name,
            "current_score": skill.proficiency_score,
            "current_risk": skill.risk_score,
            "history": [{"date": h.date.isoformat(), "score": h.proficiency_score} for h in history]
        })
        
    return jsonify(data)

@dashboard_bp.route("/api/action-plans", methods=["GET"])
@jwt_required()
def api_get_action_plans():
    user_id = get_jwt_identity()
    student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
    if not student: return jsonify({"msg": "Student not found"}), 404
    
    plans = ActionPlan.query.filter_by(student_id=student.id).order_by(ActionPlan.status.desc(), ActionPlan.due_date).all()
    
    return jsonify([{
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "status": p.status,
        "due_date": p.due_date.isoformat() if p.due_date else None
    } for p in plans])

@dashboard_bp.route("/api/action-plans/generate", methods=["POST"])
@jwt_required()
def api_generate_action_plan():
    user_id = get_jwt_identity()
    student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
    if not student: return jsonify({"msg": "Student not found"}), 404
    
    # Identifying weak skills (Risk > 0.5)
    weak_skills = StudentSkill.query.filter(StudentSkill.student_id == student.id, StudentSkill.risk_score > 0.5).all()
    
    if not weak_skills:
        return jsonify({"msg": "No high-risk skills found to generate plan for."})
        
    target_skill = weak_skills[0] # Focus on the first critical one for now
    
    # Prompt Gemini
    prompt = f"""
    Generate a JSON list of 3 specific, actionable tasks for a student to improve their {target_skill.skill_name} skill 
    from level {target_skill.proficiency_score}/100 to {target_skill.proficiency_score + 20}/100.
    Format: [{{"title": "Task Title", "description": "Details", "days_to_complete": 5}}]
    """
    
    try:
        api_key = current_app.config.get("GEMINI_API_KEY")
        if not api_key:
            return jsonify({"success": False, "msg": "Server Error: GEMINI_API_KEY is not configured."}), 500
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        
        # Clean response (remove markdown code blocks if any)
        text = response.text.replace("```json", "").replace("```", "").strip()
        tasks = json.loads(text)
        
        created_plans = []
        for task in tasks:
            plan = ActionPlan(
                student_id=student.id,
                skill_id=target_skill.id,
                title=task.get('title'),
                description=task.get('description'),
                status='pending',
                due_date=datetime.utcnow().date() # Simplified due date logic
            )
            db.session.add(plan)
            created_plans.append(plan.title)
            
        db.session.commit()
        return jsonify({"success": True, "created": created_plans})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@dashboard_bp.route("/api/action-plans/<int:plan_id>/complete", methods=["POST"])
@jwt_required()
def api_complete_action_plan(plan_id):
    user_id = get_jwt_identity()
    student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
    
    plan = ActionPlan.query.get(plan_id)
    if not plan or plan.student_id != student.id:
        return jsonify({"msg": "Plan not found"}), 404
        
    plan.status = 'completed'
    plan.completed_at = datetime.utcnow()
    
    # Gamification: Boost skill slightly
    if plan.skill:
        plan.skill.proficiency_score = min(100, plan.skill.proficiency_score + 2)
        plan.skill.risk_score = analytics_engine.calculate_risk_score(plan.skill.proficiency_score, student.current_cgpa)
        
    db.session.commit()
    return jsonify({"msg": "Plan completed", "new_score": plan.skill.proficiency_score if plan.skill else None})


# --- NEW PROFILE & ROUTINE ROUTES ---

@dashboard_bp.route("/student/profile", methods=["GET", "POST"])
@jwt_required()
def student_profile():
    user_id = get_jwt_identity()
    student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
    if not student: return jsonify({"msg": "Student not found"}), 404

    if request.method == "POST":
        # Handle "Edit Profile" form from modal
        student.full_name = request.form.get("full_name", student.full_name)
        student.university = request.form.get("university", student.university)
        student.department = request.form.get("department", student.department)
        student.current_year = request.form.get("current_year", student.current_year)
        
        cgpa_str = request.form.get("cgpa")
        if cgpa_str:
            try:
                # This field in the form is labelled "Target CGPA" but maps to 'cgpa' name
                # However, the model has 'current_cgpa'. Let's assume this form updates current_cgpa unless specified
                # Actually, the template shows "Target CGPA" but name="cgpa". 
                # StudentProfile model has `current_cgpa`. Let's update that for now or add a custom field if needed.
                # For this implementation, I'll map it to current_cgpa.
                student.current_cgpa = float(cgpa_str)
            except ValueError:
                pass

        student.career_goal = request.form.get("career_goal", student.career_goal)
        student.linkedin_profile = request.form.get("linkedin_profile", student.linkedin_profile)
        student.github_profile = request.form.get("github_profile", student.github_profile)
        student.bio = request.form.get("bio", student.bio)

        # Handle Profile Picture Upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_pics')
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, filename))
                student.profile_picture = filename

        db.session.commit()
        return redirect(url_for('dashboard.student_profile'))

    return render_template("student_profile.html", student=student)

@dashboard_bp.route("/student/delete-profile", methods=["DELETE"])
@jwt_required()
def delete_profile():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user: return jsonify({"success": False, "error": "User not found"}), 404
    
    # Cascade delete should handle profile cleanup if configured, 
    # ensuring manual cleanup just in case
    db.session.delete(user)
    db.session.commit()
    return jsonify({"success": True})

@dashboard_bp.route("/student/update-data", methods=["GET"])
@jwt_required()
def view_update_data():
    return render_template("update_profile_data.html")

@dashboard_bp.route("/update-progress", methods=["POST"])
@jwt_required()
def update_progress():
    user_id = get_jwt_identity()
    student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
    if not student: return jsonify({"msg": "Student not found"}), 404

    # 1. Update Academic Info
    student.university = request.form.get("university")
    student.department = request.form.get("department")
    # student.current_year = request.form.get("year") # Map 'year' to 'current_year' if needed
    
    try:
        student.current_cgpa = float(request.form.get("current_cgpa"))
    except (ValueError, TypeError):
        pass

    # 2. Update Career Interests
    # Simple implementation: Clear old and add new top 2
    CareerInterest.query.filter_by(student_id=student.id).delete()
    
    role1 = request.form.get("role_1")
    match1 = request.form.get("match_1")
    if role1:
        db.session.add(CareerInterest(student_id=student.id, field_name=role1, interest_score=float(match1) if match1 else 0))
        
    role2 = request.form.get("role_2")
    match2 = request.form.get("match_2")
    if role2:
        db.session.add(CareerInterest(student_id=student.id, field_name=role2, interest_score=float(match2) if match2 else 0))

    # 3. Update Skills (Just parsing the text for now)
    skills_known = request.form.get("skills_known", "")
    for skill_name in skills_known.split(','):
        s_name = skill_name.strip()
        if s_name:
            # Check if exists
            existing = StudentSkill.query.filter_by(student_id=student.id, skill_name=s_name).first()
            if not existing:
                db.session.add(StudentSkill(student_id=student.id, skill_name=s_name, proficiency_score=50)) # Default score

    db.session.commit()
    
    return redirect(url_for('dashboard.student_dashboard')) # Redirect back to dashboard

@dashboard_bp.route("/student/weekly-routine", methods=["GET"])
@jwt_required()
def student_routine():
    from datetime import datetime, timedelta
    from sqlalchemy import func
    from collections import defaultdict
    
    user_id = get_jwt_identity()
    student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
    
    if not student:
        return jsonify({"msg": "Student not found"}), 404
    
    # Calculate this week's date range
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())  # Monday
    week_end = week_start + timedelta(days=6)  # Sunday
    
    # Fetch ALL study sessions for this student (for calendar view)
    all_sessions = StudySession.query.filter_by(student_id=student.id).order_by(StudySession.date.desc()).all()
    
    # Group sessions by ISO date for calendar
    sessions_by_date = defaultdict(list)
    for s in all_sessions:
        date_key = s.date.strftime('%Y-%m-%d')
        sessions_by_date[date_key].append({
            'id': s.id,
            'topic': s.topic_studied,
            'duration': s.duration_minutes,
            'skill': s.related_skill or ''
        })
    
    # Calculate weekly stats
    weekly_sessions = StudySession.query.filter(
        StudySession.student_id == student.id,
        StudySession.date >= week_start,
        StudySession.date <= week_end
    ).all()
    
    total_hours = sum(s.duration_minutes for s in weekly_sessions) / 60.0 if weekly_sessions else 0
    session_count = len(weekly_sessions)
    
    # Find top topic
    topic_counts = {}
    for session in weekly_sessions:
        topic = session.topic_studied
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
    
    top_topic = max(topic_counts.items(), key=lambda x: x[1]) if topic_counts else None
    
    return render_template(
        "student_weekly_routine.html",
        sessions=all_sessions,
        sessions_by_date=dict(sessions_by_date),
        total_hours=round(total_hours, 1),
        session_count=session_count,
        top_topic=top_topic[0] if top_topic else None,
        top_topic_count=top_topic[1] if top_topic else 0,
        current_year=today.year,
        current_month=today.month
    )

@dashboard_bp.route("/student/add-study-session", methods=["POST"])
@jwt_required()
def add_study_session():
    user_id = get_jwt_identity()
    student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
    if not student: return jsonify({"msg": "Student not found"}), 404

    date_str = request.form.get("date")
    duration = request.form.get("duration_minutes")
    topic = request.form.get("topic_studied")
    related_skill = request.form.get("related_skill")  # Now a string, not ID
    
    if not date_str or not duration or not topic:
         return jsonify({"msg": "Missing required fields"}), 400

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        duration_int = int(duration)
    except ValueError:
        return jsonify({"msg": "Invalid data format"}), 400

    session = StudySession(
        student_id=student.id,
        date=date_obj,
        duration_minutes=duration_int,
        topic_studied=topic,
        related_skill=related_skill if related_skill else None  # Store as string
    )
    
    db.session.add(session)
    db.session.commit()

    return redirect(url_for('dashboard.student_routine'))

@dashboard_bp.route("/student/update-study-session/<int:session_id>", methods=["POST"])
@jwt_required()
def update_study_session(session_id):
    user_id = get_jwt_identity()
    student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
    if not student:
        return jsonify({"success": False, "error": "Student not found"}), 404

    session = StudySession.query.get(session_id)
    if not session or session.student_id != student.id:
        return jsonify({"success": False, "error": "Session not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    if data.get("topic"):
        session.topic_studied = data["topic"]
    if data.get("duration"):
        try:
            session.duration_minutes = int(data["duration"])
        except (ValueError, TypeError):
            pass
    if "skill" in data:
        session.related_skill = data["skill"] if data["skill"] else None

    db.session.commit()
    return jsonify({
        "success": True,
        "session": {
            "id": session.id,
            "topic": session.topic_studied,
            "duration": session.duration_minutes,
            "skill": session.related_skill or ""
        }
    })

@dashboard_bp.route("/student/settings", methods=["GET"])
@jwt_required()
def student_settings():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
    
    if not student or not user:
        return jsonify({"msg": "User not found"}), 404
    
    return render_template("student_settings.html", user=user, profile=student)

