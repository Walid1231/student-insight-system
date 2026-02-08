from flask import Blueprint, render_template, jsonify, request, redirect, url_for, current_app
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from models import db, User, StudentProfile, AcademicMetric, StudentSkill, StudentCourse, CareerInterest, AnalyticsResult, StudyActivity
from datetime import datetime
from ml.analytics_engine import AnalyticsEngine
import os
from werkzeug.utils import secure_filename

dashboard_bp = Blueprint("dashboard", __name__)
analytics_engine = AnalyticsEngine()

@dashboard_bp.route("/student/dashboard")
@jwt_required()
def student_dashboard():
    claims = get_jwt()
    role = claims.get("role")
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404
    user_id = user.id

    student = StudentProfile.query.filter_by(user_id=user_id).first()
    if not student:
        student = StudentProfile.query.filter_by(id=user_id).first()
    
    # If no profile exists yet (new user), possibly redirect to create profile
    # For now, we render the dashboard with empty/default data handled by Jinja/JS
    
    return render_template("student_dashboard.html", student=student)

@dashboard_bp.route("/student/profile", methods=["GET", "POST"])
@jwt_required()
def student_profile():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404
        
    student = StudentProfile.query.filter_by(user_id=user.id).first()
    if not student:
        # Create default if not exists
        claims = get_jwt()
        name = claims.get("name", user.name)
        student = StudentProfile(user_id=user.id, full_name=name, email=email)
        db.session.add(student)
        db.session.commit()

    if request.method == "POST":
        # Handle Profile Picture
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename != '':
                filename = secure_filename(f"user_{user.id}_{file.filename}")
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_pics')
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, filename))
                student.profile_picture = filename

        # Update Text Fields
        student.introduction = request.form.get("introduction")
        student.university = request.form.get("university")
        student.school = request.form.get("school")
        student.college = request.form.get("college") # If applicable
        student.linkedin_link = request.form.get("linkedin")
        student.facebook_link = request.form.get("facebook")
        
        # Also allow updating name/dept if needed
        student.full_name = request.form.get("full_name", student.full_name)
        student.department = request.form.get("department", student.department)

        db.session.commit()
        return redirect(url_for('dashboard.student_profile'))

    return render_template("student_profile.html", student=student, user=user)

@dashboard_bp.route("/student/weekly-routine")
@jwt_required()
def weekly_routine():
    return render_template("student_weekly_routine.html")

@dashboard_bp.route("/student/dashboard/v2")
@jwt_required()
def student_dashboard_v2():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404
    user_id = user.id
    
    student = StudentProfile.query.filter_by(user_id=user_id).first()
    if not student:
         # Fallback to id=user_id for legacy data
         student = StudentProfile.query.filter_by(id=user_id).first()
    
    if not student:
        # Redirect to data entry if no profile exists
        return redirect(url_for('dashboard.update_progress'))

    # Fetch Real Data
    metric = AcademicMetric.query.filter_by(student_id=student.id).first()
    courses = StudentCourse.query.filter_by(student_id=student.id).all()
    skills = StudentSkill.query.filter_by(student_id=student.id).all()
    careers = CareerInterest.query.filter_by(student_id=student.id).all()
    activities = StudyActivity.query.filter_by(student_id=student.id).order_by(StudyActivity.date).all()

    # Process Data for Template
    
    # 1. Weekly Hours (ensure 7 days)
    # This is a simple implementation. For production, align with actual Mon-Sun dates.
    weekly_hours = [0] * 7
    if activities:
        # Taking last 7 entries for simplicity
        recent_acts = activities[-7:]
        weekly_hours = [act.hours for act in recent_acts]
        # Pad if less than 7
        while len(weekly_hours) < 7:
            weekly_hours.insert(0, 0)

    # 2. Goal Probability (Simple Mock Logic based on real data)
    goal_prob = 50 
    if metric and metric.target_gpa and student.current_cgpa:
        diff = metric.target_gpa - student.current_cgpa
        if diff <= 0: goal_prob = 99
        elif diff < 0.2: goal_prob = 85
        elif diff < 0.5: goal_prob = 60
        else: goal_prob = 40
    
    # 3. Skills Separation
    skills_known = [s.skill_name for s in skills if not s.is_target]
    skills_todo = [s.skill_name for s in skills if s.is_target]

    data = {
        "name": student.full_name,
        "department": student.department or "General",
        "university_name": student.university or "University",
        "year": "Current", # could add year field to model if needed
        "status": "On Track" if goal_prob > 70 else "At Risk",
        "cgpa": student.current_cgpa or 0.0,
        "credits_completed": (metric.total_credits or 0) if metric else 0,
        "subjects": [{"name": c.course_name, "score": c.score or 0, "grade": c.grade} for c in courses],
        "careers": [{"role": c.role_name, "match": c.match_score} for c in careers],
        "skills_known": skills_known,
        "skills_todo": skills_todo,
        "weekly_hours": weekly_hours,
        "goal_prob": goal_prob,
        "target_gpa": metric.target_gpa if metric else 4.0,
        "time_to_goal": "End of Semester",
        "guidance_msg": "Great job updating your profile! Keep tracking your study hours to see accurate trends.",
        "guidance_tip": "Consistency is key. Try to study at the same time every day."
    }
    return render_template("student_dashboard_v2.html", data=data)

@dashboard_bp.route("/update-progress", methods=["GET", "POST"])
@jwt_required()
def update_progress():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404
    user_id = user.id # valid user ID
    
    # Check if student profile exists, if not create one linked to user
    # (Assuming User model is linked, but here we use user_id directly as student_id for simplicity 
    # OR we need to find the student profile linked to this user_id)
    # The models say: User -> StudentProfile (One-to-One)
    # dashboard/routes.py:19 implies `user_id` from jwt is `id`, and we query StudentProfile by id=user_id? 
    # Wait, existing code: `student = StudentProfile.query.filter_by(id=user_id).first()`
    # If user_id is the Primary Key of User table, StudentProfile has user_id FK.
    # So correct query should be `filter_by(user_id=user_id)` IF they are linked that way.
    # However, existing code at line 19 used `id=user_id`. I will follow existing pattern but add a check.
    
    # Let's assume user_id from JWT is the User.id.
    # And StudentProfile might share the same ID or be linked.
    # Given line 19: `student = StudentProfile.query.filter_by(id=user_id).first()`
    # It seems the system assumes StudentProfile.id == User.id (which happens if manually synced)
    # OR the previous dev made a mistake.
    # SAFE BET: Query by user_id if column exists (it does, line 34 models.py).
    
    # Correcting logic to be robust:
    student = StudentProfile.query.filter_by(user_id=user_id).first()
    if not student:
        # Fallback to id=user_id if user_id field is empty (legacy support)
         student = StudentProfile.query.filter_by(id=user_id).first()
    
    # If still no student, strictly speaking we should create one based on User info or error.
    # For this task, I'll assume we can create/update.

    if request.method == "POST":
        if not student:
            # Create new profile
            claims = get_jwt()
            name = claims.get("name", "Student")
            email = claims.get("sub") # identity is email usually, or we query User
            student = StudentProfile(user_id=user_id, full_name=name, email=email)
            db.session.add(student)
            db.session.commit() # Commit to get ID
        
        # 1. Update Profile
        student.university = request.form.get("university")
        student.department = request.form.get("department")
        student.current_cgpa = float(request.form.get("current_cgpa") or 0)
        
        # 2. Update Metrics
        metric = AcademicMetric.query.filter_by(student_id=student.id).first()
        if not metric:
            metric = AcademicMetric(student_id=student.id)
            db.session.add(metric)
        metric.target_gpa = float(request.form.get("target_gpa") or 0)
        
        # 3. Update Courses (Clear old, add new for simplicity)
        StudentCourse.query.filter_by(student_id=student.id).delete()
        for i in range(1, 4): # 3 subjects
            sub = request.form.get(f"subject_{i}")
            score = request.form.get(f"score_{i}")
            if sub and score:
                try:
                    score_val = int(score)
                except ValueError:
                    score_val = 0
                    
                grade = "A" if score_val > 80 else "B" # Simple logic
                course = StudentCourse(student_id=student.id, course_name=sub, score=score_val, grade=grade, course_type='strong')
                db.session.add(course)

        # 4. Update Careers
        CareerInterest.query.filter_by(student_id=student.id).delete()
        for i in range(1, 3):
            role = request.form.get(f"role_{i}")
            match = request.form.get(f"match_{i}")
            # Ensure both fields are present and match is a number
            if role and match:
                try:
                    match_val = int(match)
                except ValueError:
                    match_val = 0
                ci = CareerInterest(student_id=student.id, role_name=role, match_score=match_val)
                db.session.add(ci)

        # 5. Update Skills
        StudentSkill.query.filter_by(student_id=student.id).delete()
        # Known
        known = request.form.get("skills_known", "").split(",")
        for k in known:
            if k.strip():
                db.session.add(StudentSkill(student_id=student.id, skill_name=k.strip(), is_target=False))
        # Todo
        todo = request.form.get("skills_todo", "").split(",")
        for t in todo:
            if t.strip():
                db.session.add(StudentSkill(student_id=student.id, skill_name=t.strip(), is_target=True))

        # 6. Study History (Mocking 7 days based on input for Mon-Sun)
        StudyActivity.query.filter_by(student_id=student.id).delete()
        days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        for idx, d in enumerate(days):
            h_val = request.form.get(f"h_{d}")
            try:
                h_float = float(h_val) if h_val and h_val.strip() else 0.0
            except ValueError:
                h_float = 0.0
                
            # Create dummy date for last week
            # In real app, we would map this to actual dates relative to today
            sa = StudyActivity(student_id=student.id, hours=h_float, date=datetime.utcnow()) 
            db.session.add(sa)

        db.session.commit()
        return redirect(url_for('dashboard.student_dashboard_v2'))

    return render_template("update_profile_data.html")

@dashboard_bp.route("/api/student/analytics")
@jwt_required()
def student_analytics_api():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404
    user_id = user.id # user_id is now the ID, not email
    
    # Get basic data using resolved student profile
    student = StudentProfile.query.filter_by(user_id=user_id).first()
    if not student:
        # Fallback
        student = StudentProfile.query.filter_by(id=user_id).first()
        
    metric = AcademicMetric.query.filter_by(student_id=student.id).first() if student else None
    
    # If no data found, return empty structure or error
    if not metric:
        # Fallback for demo: return dummy data for Student 1 if current user has no data?
        # Better: return empty/default data structure to avoid frontend errors
        return jsonify({
            "cgpa": 0.0,
            "rank": 0,
            "credits": 0,
            "skills_count": 0,
            "gpa_trend": [],
            "career_interests": {},
            "top_skills": [],
            "strong_courses": [],
            "weak_courses": [],
            "recommendations": []
        })
        
    skills = StudentSkill.query.filter_by(student_id=student.id).all() if student else []
    courses = StudentCourse.query.filter_by(student_id=student.id).all() if student else []
    
    # Run ML prediction
    analytics_data = analytics_engine.generate_insight_report(user_id)
    
    response_data = {
        "cgpa": metric.student.current_cgpa,
        "rank": metric.department_rank,
        "credits": metric.total_credits,
        "skills_count": len(skills),
        "gpa_trend": metric.get_gpas(),
        "career_interests": analytics_data['career_scores'],
        "top_skills": [s.skill_name for s in skills],
        "strong_courses": [{"name": c.course_name, "grade": c.grade} for c in courses if c.course_type == 'strong'],
        "weak_courses": [{"name": c.course_name, "grade": c.grade} for c in courses if c.course_type == 'weak'],
        "recommendations": analytics_data['recommendations']
    }
    
    return jsonify(response_data)


@dashboard_bp.route("/teacher/dashboard")
@jwt_required()
def teacher_dashboard():
    claims = get_jwt()
    role = claims.get("role")

    if role != "teacher":
        return jsonify({"msg": "Access denied"}), 403

    return render_template("teacher_dashboard.html")


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

            return jsonify({"success": True, "report": report_html})

        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # GET request - render the form page
    return render_template("student_insight_form.html")
