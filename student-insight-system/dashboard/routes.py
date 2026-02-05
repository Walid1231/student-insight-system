from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from models import StudentProfile, AcademicMetric, StudentSkill, StudentCourse, CareerInterest, AnalyticsResult
from ml.analytics_engine import AnalyticsEngine

dashboard_bp = Blueprint("dashboard", __name__)
analytics_engine = AnalyticsEngine()

@dashboard_bp.route("/student/dashboard")
@jwt_required()
def student_dashboard():
    claims = get_jwt()
    role = claims.get("role")
    user_id = get_jwt_identity()

    if role != "student":
        return jsonify({"msg": "Access denied"}), 403

    student = StudentProfile.query.filter_by(id=user_id).first()
    
    # If no profile exists yet (new user), possibly redirect to create profile
    # For now, we render the dashboard with empty/default data handled by Jinja/JS
    
    return render_template("student_dashboard.html", student=student)

@dashboard_bp.route("/api/student/analytics")
@jwt_required()
def student_analytics_api():
    user_id = get_jwt_identity()
    
    # Get basic data
    metric = AcademicMetric.query.filter_by(student_id=user_id).first()
    
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
        
    skills = StudentSkill.query.filter_by(student_id=user_id).all()
    courses = StudentCourse.query.filter_by(student_id=user_id).all()
    
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
