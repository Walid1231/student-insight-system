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
# DEPARTMENT → CAREERS & SKILLS REFERENCE DATA
# =============================================================

DEPT_CAREERS_SKILLS = {
    "Computer Science & Engineering (CSE)": {
        "careers": [
            "Software Developer", "Web Developer", "Mobile App Developer",
            "Data Scientist", "AI / Machine Learning Engineer",
            "Cybersecurity Specialist", "Cloud Engineer", "DevOps Engineer",
            "Game Developer", "Database Administrator", "Systems Analyst",
            "IT Project Manager", "University Lecturer / Researcher",
        ],
        "skills": [
            "Python", "Java", "C++", "JavaScript", "SQL", "HTML/CSS",
            "React", "Node.js", "Git", "Docker", "Linux",
            "Data Structures", "Algorithms", "Machine Learning",
            "Data Analysis", "Cloud Computing", "Web Development",
            "Cybersecurity", "REST APIs", "Databases",
        ],
    },
    "Software Engineering": {
        "careers": [
            "Software Developer", "Web Developer", "Mobile App Developer",
            "Data Scientist", "AI / Machine Learning Engineer",
            "Cybersecurity Specialist", "Cloud Engineer", "DevOps Engineer",
            "Game Developer", "Database Administrator", "Systems Analyst",
            "IT Project Manager", "University Lecturer / Researcher",
        ],
        "skills": [
            "Python", "Java", "C#", "JavaScript", "TypeScript", "SQL",
            "React", "Spring Boot", "Docker", "Kubernetes", "Git",
            "Agile / Scrum", "REST APIs", "System Design", "Testing",
        ],
    },
    "Electrical & Electronic Engineering (EEE)": {
        "careers": [
            "Electrical Engineer", "Power System Engineer", "Electronics Engineer",
            "Telecommunications Engineer", "Embedded Systems Engineer",
            "Robotics Engineer", "Automation Engineer", "Renewable Energy Engineer",
            "Research Engineer", "Engineering Consultant",
        ],
        "skills": [
            "Circuit Analysis", "MATLAB", "Control Systems", "Embedded Systems",
            "Arduino", "Signal Processing", "Power Systems", "PCB Design",
            "PLC Programming", "AutoCAD Electrical", "VHDL", "Microcontrollers",
            "Communication", "Problem Solving", "Critical Thinking",
        ],
    },
    "Civil Engineering": {
        "careers": [
            "Structural Engineer", "Construction Engineer", "Transportation Engineer",
            "Urban Planner", "Environmental Engineer", "Geotechnical Engineer",
            "Project Manager (Construction)", "Site Engineer", "Government Engineer",
        ],
        "skills": [
            "AutoCAD Civil", "Structural Analysis", "Revit", "Surveying", "GIS",
            "Concrete Design", "Project Scheduling", "Construction Management",
            "Geotechnical Analysis", "ETABS", "Highway Design",
            "Environmental Engineering", "Problem Solving", "Project Management",
        ],
    },
    "Mechanical Engineering": {
        "careers": [
            "Mechanical Engineer", "Manufacturing Engineer", "Automotive Engineer",
            "Aerospace Engineer", "Energy Systems Engineer", "Robotics Engineer",
            "Maintenance Engineer", "Product Design Engineer",
        ],
        "skills": [
            "AutoCAD", "SolidWorks", "ANSYS", "Thermodynamics", "Fluid Mechanics",
            "CNC Machining", "MATLAB", "3D Modeling", "Materials Science",
            "Manufacturing Processes", "FEA Analysis", "Robot Programming",
            "Problem Solving", "Critical Thinking",
        ],
    },
    "Information Technology (IT)": {
        "careers": [
            "IT Support Specialist", "Network Administrator", "Systems Administrator",
            "Cloud Engineer", "Cybersecurity Analyst", "Database Administrator",
            "IT Project Manager", "Business Analyst",
        ],
        "skills": [
            "Networking", "Cybersecurity", "Windows Server", "Linux",
            "Cloud Computing", "Virtualization", "IT Support",
            "Database Administration", "Active Directory",
            "Cisco Networking", "Python", "PowerShell",
        ],
    },
    "Industrial & Production Engineering (IPE)": {
        "careers": [
            "Industrial Engineer", "Production Manager", "Quality Assurance Engineer",
            "Supply Chain Analyst", "Operations Manager", "Process Improvement Engineer",
        ],
        "skills": [
            "Lean Manufacturing", "Six Sigma", "AutoCAD", "MATLAB", "ERP Systems",
            "Project Management", "Supply Chain Management", "Quality Control",
            "Operations Research", "Simulation Tools", "Teamwork",
        ],
    },
    "Business Administration (BBA)": {
        "careers": [
            "Business Manager", "Marketing Manager", "Financial Analyst",
            "HR Manager", "Operations Manager", "Business Consultant",
            "Entrepreneur / Startup Founder", "Supply Chain Manager",
            "Corporate Executive",
        ],
        "skills": [
            "Business Strategy", "Marketing", "Sales", "Supply Chain",
            "Excel Advanced", "Business Communication", "Economics",
            "Market Research", "SAP ERP", "Digital Marketing",
            "Leadership", "Project Management", "Teamwork",
        ],
    },
    "Accounting": {
        "careers": [
            "Accountant", "Auditor", "Financial Analyst", "Investment Banker",
            "Tax Consultant", "Chartered Accountant", "Risk Analyst", "Banking Officer",
        ],
        "skills": [
            "Financial Analysis", "Accounting", "Bloomberg Terminal",
            "Excel Advanced", "Corporate Finance", "Financial Reporting",
            "QuickBooks", "Taxation", "Auditing", "Cost Accounting",
            "Communication", "Critical Thinking",
        ],
    },
    "Finance": {
        "careers": [
            "Accountant", "Auditor", "Financial Analyst", "Investment Banker",
            "Tax Consultant", "Chartered Accountant", "Risk Analyst", "Banking Officer",
        ],
        "skills": [
            "Financial Modelling", "Accounting", "Bloomberg Terminal",
            "Investment Analysis", "Risk Management", "Excel Advanced",
            "Corporate Finance", "Derivatives", "Portfolio Management",
            "Financial Reporting", "QuickBooks",
        ],
    },
    "Marketing": {
        "careers": [
            "Marketing Manager", "Digital Marketing Specialist", "Brand Manager",
            "Content Strategist", "SEO Specialist", "Social Media Manager",
            "Market Research Analyst", "Product Manager",
        ],
        "skills": [
            "Digital Marketing", "SEO / SEM", "Content Marketing", "Social Media",
            "Google Analytics", "Market Research", "Branding", "Copywriting",
            "Email Marketing", "CRM Tools", "Communication", "Creativity",
        ],
    },
    "Management": {
        "careers": [
            "Operations Manager", "Project Manager", "Consultant",
            "HR Manager", "General Manager", "Team Lead",
            "Entrepreneur / Startup Founder",
        ],
        "skills": [
            "Leadership", "Project Management", "Teamwork", "Communication",
            "Problem Solving", "Strategic Planning", "Decision Making",
            "Negotiation", "Microsoft Office", "Time Management",
        ],
    },
    "Human Resource Management (HRM)": {
        "careers": [
            "HR Manager", "Recruiter", "Talent Acquisition Specialist",
            "Training & Development Manager", "Compensation & Benefits Analyst",
            "HR Business Partner", "Organizational Development Specialist",
        ],
        "skills": [
            "Recruitment", "Employee Relations", "Performance Management",
            "Training & Development", "HR Analytics", "Labor Law",
            "Communication", "Leadership", "Microsoft Office", "Teamwork",
        ],
    },
    "Mathematics": {
        "careers": [
            "Data Analyst", "Data Scientist", "Statistician",
            "Actuary", "University Lecturer", "Research Scientist",
            "Operations Research Analyst", "Financial Analyst",
        ],
        "skills": [
            "Python", "R", "MATLAB", "Statistics", "Linear Algebra",
            "Calculus", "Numerical Methods", "Machine Learning",
            "Data Analysis", "Problem Solving", "Critical Thinking", "Research",
        ],
    },
    "Physics": {
        "careers": [
            "Research Scientist", "University Lecturer / Researcher",
            "Medical Physicist", "Data Analyst", "Optics Engineer",
            "Semiconductor Engineer",
        ],
        "skills": [
            "MATLAB", "Python", "Research", "Laboratory Skills",
            "Data Analysis", "Quantum Mechanics", "Electromagnetism",
            "Problem Solving", "Critical Thinking", "Mathematics",
        ],
    },
    "Chemistry": {
        "careers": [
            "Research Chemist", "Chemical Engineer", "Quality Control Analyst",
            "Pharmaceutical Researcher", "Environmental Chemist",
            "University Lecturer / Researcher",
        ],
        "skills": [
            "Laboratory Skills", "Research", "Analytical Chemistry",
            "Organic Chemistry", "Mass Spectrometry", "Python",
            "Data Analysis", "Problem Solving", "Critical Thinking",
        ],
    },
    "Statistics": {
        "careers": [
            "Data Analyst", "Data Scientist", "Statistician",
            "Machine Learning Engineer", "Business Intelligence Analyst",
            "Risk Analyst",
        ],
        "skills": [
            "Python", "R", "SQL", "Machine Learning", "Deep Learning",
            "Statistics", "Data Visualization", "Pandas", "NumPy",
            "Power BI", "Tableau", "Research",
        ],
    },
    "Biotechnology": {
        "careers": [
            "Biotechnologist", "Research Scientist", "Bioinformatician",
            "Pharmaceutical Researcher", "Quality Control Scientist",
            "University Lecturer / Researcher",
        ],
        "skills": [
            "Molecular Biology", "Genetics", "Bioinformatics",
            "Laboratory Skills", "Python", "R", "Research",
            "Data Analysis", "Critical Thinking", "Communication",
        ],
    },
    "Environmental Science": {
        "careers": [
            "Environmental Consultant", "Environmental Engineer",
            "Policy Analyst", "Research Scientist", "Government Advisor",
            "NGO Specialist",
        ],
        "skills": [
            "GIS", "Environmental Impact Assessment", "Research",
            "Data Analysis", "Policy Writing", "Laboratory Skills",
            "Communication", "Project Management",
        ],
    },
    "English": {
        "careers": [
            "Teacher / Lecturer", "Journalist", "Content Writer",
            "Editor / Publisher", "Public Relations Specialist",
            "Translator", "Media Professional",
        ],
        "skills": [
            "Creative Writing", "Academic Writing", "Research",
            "Public Speaking", "Editing", "Translation",
            "Communication", "Presentation", "Critical Thinking",
        ],
    },
    "Bangla": {
        "careers": [
            "Teacher / Lecturer", "Journalist", "Author / Writer",
            "Editor", "Cultural Researcher", "Translator",
        ],
        "skills": [
            "Creative Writing", "Research", "Journalism",
            "Communication", "Editing", "Presentation",
            "Critical Thinking", "Leadership",
        ],
    },
    "History": {
        "careers": [
            "Historian", "University Lecturer / Researcher", "Museum Curator",
            "Archivist", "Policy Analyst", "Journalist",
        ],
        "skills": [
            "Research", "Academic Writing", "Critical Thinking",
            "Communication", "Presentation", "Data Analysis",
        ],
    },
    "Philosophy": {
        "careers": [
            "University Lecturer / Researcher", "Ethicist", "Policy Analyst",
            "Writer / Author", "Human Rights Advocate",
        ],
        "skills": [
            "Critical Thinking", "Academic Writing", "Research",
            "Communication", "Leadership", "Presentation",
        ],
    },
    "Economics": {
        "careers": [
            "Economist", "Policy Analyst", "Research Analyst",
            "Financial Analyst", "Development Specialist",
            "Data Analyst", "Government Economic Advisor",
        ],
        "skills": [
            "Economic Modelling", "R", "Python", "Statistics",
            "Research", "Data Analysis", "Policy Writing",
            "Excel Advanced", "Communication", "Critical Thinking",
        ],
    },
    "Sociology": {
        "careers": [
            "Sociologist", "Social Worker", "NGO Specialist",
            "Policy Analyst", "Research Analyst", "Community Developer",
        ],
        "skills": [
            "Research", "Data Analysis", "Communication",
            "Community Outreach", "Presentation", "Critical Thinking",
            "Project Management",
        ],
    },
    "Political Science": {
        "careers": [
            "Political Analyst", "Policy Advisor", "Government Officer",
            "Diplomat", "Journalist", "NGO Specialist",
            "University Lecturer / Researcher",
        ],
        "skills": [
            "Research", "Policy Writing", "Communication",
            "Critical Thinking", "Presentation", "Data Analysis",
            "Leadership",
        ],
    },
    "International Relations": {
        "careers": [
            "Diplomat", "Foreign Service Officer", "Policy Analyst",
            "International Development Specialist", "NGO Specialist",
            "Journalist", "University Lecturer / Researcher",
        ],
        "skills": [
            "Research", "Policy Writing", "Communication",
            "Negotiation", "Cross-Cultural Communication", "Languages",
            "Presentation", "Critical Thinking", "Leadership",
        ],
    },
    "Public Administration": {
        "careers": [
            "Government Officer", "Policy Analyst", "Public Administrator",
            "NGO Manager", "Civil Servant", "Development Specialist",
        ],
        "skills": [
            "Public Policy", "Administration", "Leadership",
            "Communication", "Research", "Project Management",
            "Microsoft Office", "Teamwork",
        ],
    },
    "Pharmacy": {
        "careers": [
            "Pharmacist", "Drug Research Scientist",
            "Pharmaceutical Industry Manager", "Clinical Researcher",
            "Regulatory Affairs Specialist", "Quality Control Analyst",
        ],
        "skills": [
            "Pharmacology", "Biochemistry", "Laboratory Skills",
            "Clinical Research", "Regulatory Affairs", "Quality Control",
            "Research", "Communication", "Critical Thinking", "Data Analysis",
        ],
    },
    "Public Health": {
        "careers": [
            "Public Health Officer", "Epidemiologist", "Health Policy Analyst",
            "NGO Health Specialist", "Community Health Worker",
            "Research Scientist",
        ],
        "skills": [
            "Epidemiology", "Research", "Data Analysis", "Policy Writing",
            "Community Outreach", "Communication", "Microsoft Office",
            "Project Management",
        ],
    },
    "Nursing": {
        "careers": [
            "Registered Nurse", "Clinical Nurse Specialist",
            "Nurse Educator", "Healthcare Administrator",
            "Community Health Nurse",
        ],
        "skills": [
            "Clinical Skills", "Patient Care", "First Aid",
            "Communication", "Teamwork", "Critical Thinking",
            "Medical Ethics", "EMR Systems",
        ],
    },
    "Law (LLB)": {
        "careers": [
            "Lawyer / Advocate", "Legal Consultant", "Judge",
            "Corporate Legal Advisor", "Public Prosecutor",
            "Legal Researcher", "Human Rights Lawyer",
        ],
        "skills": [
            "Legal Research", "Case Analysis", "Contract Law",
            "Communication", "Negotiation", "Critical Thinking",
            "Academic Writing", "Presentation", "Leadership",
        ],
    },
}

# Grouped for the HTML <optgroup> select
DEPT_GROUPS = [
    ("💻 Engineering & Technology", [
        "Computer Science & Engineering (CSE)",
        "Electrical & Electronic Engineering (EEE)",
        "Civil Engineering",
        "Mechanical Engineering",
        "Software Engineering",
        "Information Technology (IT)",
        "Industrial & Production Engineering (IPE)",
    ]),
    ("📊 Business & Management", [
        "Business Administration (BBA)",
        "Accounting",
        "Finance",
        "Marketing",
        "Management",
        "Human Resource Management (HRM)",
    ]),
    ("🔬 Science", [
        "Mathematics",
        "Physics",
        "Chemistry",
        "Statistics",
        "Biotechnology",
        "Environmental Science",
    ]),
    ("📚 Arts & Humanities", [
        "English",
        "Bangla",
        "History",
        "Philosophy",
    ]),
    ("🌍 Social Science", [
        "Economics",
        "Sociology",
        "Political Science",
        "International Relations",
        "Public Administration",
    ]),
    ("⚕️ Health & Pharmacy", [
        "Pharmacy",
        "Public Health",
        "Nursing",
    ]),
    ("⚖️ Law", [
        "Law (LLB)",
    ]),
]


# =============================================================
# API: Department → Careers & Skills
# =============================================================

@dashboard_bp.route("/api/department-data")
@require_role("student")
def api_department_data():
    dept = request.args.get("dept", "").strip()
    data = DEPT_CAREERS_SKILLS.get(dept, {"careers": [], "skills": []})
    return jsonify(data)


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
    data["dept_groups"] = DEPT_GROUPS
    data["dept_keys"] = list(DEPT_CAREERS_SKILLS.keys())
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


# =============================================================
# JSON AJAX ENDPOINTS — Goals & Grades (no page refresh)
# =============================================================

@dashboard_bp.route("/api/gg/skill/add", methods=["POST"])
@require_role("student")
def api_gg_add_skill():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    name = data.get("skill_name", "").strip()
    if not name:
        return jsonify({"ok": False, "msg": "Skill name required"}), 400
    AcademicService.add_skill(user_id, name)
    from models import StudentSkill, StudentProfile
    student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
    skills = StudentSkill.query.filter_by(student_id=student.id).all()
    return jsonify({
        "ok": True,
        "skills": [{"id": s.id, "name": s.skill_name} for s in skills],
    })


@dashboard_bp.route("/api/gg/skill/<int:skill_id>/delete", methods=["POST"])
@require_role("student")
def api_gg_delete_skill(skill_id):
    user_id = get_jwt_identity()
    AcademicService.remove_skill(user_id, skill_id)
    from models import StudentSkill, StudentProfile
    student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
    skills = StudentSkill.query.filter_by(student_id=student.id).all()
    return jsonify({
        "ok": True,
        "skills": [{"id": s.id, "name": s.skill_name} for s in skills],
    })


@dashboard_bp.route("/api/gg/goal/add", methods=["POST"])
@require_role("student")
def api_gg_add_goal():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    career_id = data.get("career_id")
    goal_type = data.get("goal_type", "Long Term")
    if not career_id:
        return jsonify({"ok": False, "msg": "career_id required"}), 400
    AcademicService.add_goal(user_id, int(career_id), goal_type)
    return jsonify({"ok": True})


@dashboard_bp.route("/api/gg/goal/<int:goal_id>/delete", methods=["POST"])
@require_role("student")
def api_gg_delete_goal(goal_id):
    user_id = get_jwt_identity()
    AcademicService.delete_goal(user_id, goal_id)
    return jsonify({"ok": True})


@dashboard_bp.route("/api/gg/goal/<int:goal_id>/primary", methods=["POST"])
@require_role("student")
def api_gg_set_primary(goal_id):
    user_id = get_jwt_identity()
    AcademicService.set_primary_goal(user_id, goal_id)
    return jsonify({"ok": True})


@dashboard_bp.route("/api/gg/target-cgpa", methods=["POST"])
@require_role("student")
def api_gg_save_target_cgpa():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    target = data.get("target_cgpa")
    if target is None:
        return jsonify({"ok": False, "msg": "target_cgpa required"}), 400
    AcademicService.save_target_cgpa(user_id, float(target))
    return jsonify({"ok": True})


@dashboard_bp.route("/api/gg/grade/add", methods=["POST"])
@require_role("student")
def api_gg_add_grade():
    from schemas.academic import GradeInput
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    try:
        payload = GradeInput(
            course_name=data.get("course_name", ""),
            course_type=data.get("course_type", "Core"),
            credit_value=int(data.get("credit_value", 3)),
            semester=int(data.get("semester", 1)),
            grade=data.get("grade", ""),
        )
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 400
    AcademicService.add_grade(user_id, payload)
    from models import StudentProfile
    student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
    return jsonify({"ok": True, "new_cgpa": student.current_cgpa})


@dashboard_bp.route("/api/gg/grade/<int:record_id>/delete", methods=["POST"])
@require_role("student")
def api_gg_delete_grade(record_id):
    user_id = get_jwt_identity()
    AcademicService.delete_grade(user_id, record_id)
    from models import StudentProfile
    student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
    return jsonify({"ok": True, "new_cgpa": student.current_cgpa})


@dashboard_bp.route("/api/gg/state", methods=["GET"])
@require_role("student")
def api_gg_state():
    """Return full current state for Goals & Grades page (for re-render after actions)."""
    user_id = get_jwt_identity()
    data = AcademicService.get_goals_grades_data(user_id)
    student = data["student"]
    return jsonify({
        "ok": True,
        "current_cgpa": student.current_cgpa,
        "target_cgpa": student.target_cgpa,
        "skills": [{"id": s.id, "name": s.skill_name} for s in data["student_skills"]],
        "goals": data["goals"],
        "records": data["records"],
        "matching_careers": [
            {
                "id": c["id"],
                "title": c["title"],
                "field_category": c["field_category"],
                "match_count": c["match_count"],
                "goal_id": c["goal_id"],
            }
            for c in data["matching_careers"]
        ],
    })

