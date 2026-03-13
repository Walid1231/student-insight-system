"""
seed.py — Unified Seed Script for Student Insight System
=========================================================
Replaces: seed_students.py, seed_20_students.py, populate_teacher_dashboard.py,
          populate_dashboard_data.py, populate_test_data_phase2.py,
          scripts/seed_skills.py, scripts/seed_skills_by_dept.py

Usage:
    python seed.py                    # Run all sections
    python seed.py --students         # Only seed 8 demo students
    python seed.py --teacher          # Only seed 1 teacher + 7 students (with assignments/attendance/notes)
    python seed.py --skills-catalog   # Only populate the Skill catalog (by department)
    python seed.py --students --skills-catalog  # Combine flags

Every section is idempotent: safe to re-run, skips existing rows.
"""

import sys
import argparse
import random
import json
from datetime import date, datetime, timedelta

from app import create_app
app = create_app()
from models import (
    db, User, StudentProfile, TeacherProfile, TeacherAssignment,
    AcademicMetric, StudentAcademicRecord, CourseCatalog,
    StudentSkill, WeeklyUpdate, StudySession, StudentGoal,
    CareerPath, CareerInterest, StudentAlert, StudentNote,
    Attendance, Assignment, AssignmentSubmission,
    AssessmentResult, AnalyticsResult,
)
from werkzeug.security import generate_password_hash

# ─────────────────────────────────────────────────────────────────────────────
#  Shared reference data
# ─────────────────────────────────────────────────────────────────────────────

COURSES = [
    ("Calculus I",               "Mathematics",       "Core",     3),
    ("Calculus II",              "Mathematics",       "Core",     3),
    ("Linear Algebra",           "Mathematics",       "Core",     3),
    ("Introduction to Python",   "Computer Science",  "Core",     3),
    ("Data Structures",          "Computer Science",  "Core",     3),
    ("Algorithms",               "Computer Science",  "Core",     3),
    ("Database Systems",         "Computer Science",  "Core",     3),
    ("English Composition",      "General Education", "GED",      2),
    ("Technical Writing",        "General Education", "GED",      2),
    ("Physics I",                "Engineering",       "Core",     3),
    ("Physics II",               "Engineering",       "Core",     3),
    ("Circuit Analysis",         "Engineering",       "Core",     3),
    ("Microeconomics",           "Business",          "GED",      3),
    ("Macroeconomics",           "Business",          "GED",      3),
    ("Statistics",               "Mathematics",       "Core",     3),
    ("Machine Learning",         "Computer Science",  "Elective", 3),
    ("Web Development",          "Computer Science",  "Elective", 3),
    ("Digital Marketing",        "Business",          "Elective", 3),
    ("Ethics in Technology",     "General Education", "GED",      2),
    ("Research Methods",         "General Education", "GED",      2),
]

CAREERS = [
    ("Software Engineer",          "IT"),
    ("Data Scientist",             "Data Science"),
    ("Electrical Engineer",        "Engineering"),
    ("Business Analyst",           "Business"),
    ("UX Designer",                "Design"),
    ("Cybersecurity Analyst",      "IT"),
    ("Product Manager",            "Business"),
    ("Machine Learning Engineer",  "AI"),
]

# 8 diverse students (idempotent by email)
STUDENTS = [
    {
        "name": "Ahmed Al-Rashid", "email": "ahmed.rashid@student.edu",
        "dept": "Computer Science", "class_lvl": "3", "section": "A",
        "cgpa": 3.85, "target": 4.0, "semester": 6, "credits": 72,
        "career_idx": 0, "gpa_trend": [3.6, 3.7, 3.8, 3.85],
        "skills": [("Python", 90, 0.10), ("Data Analysis", 80, 0.20), ("SQL", 75, 0.25)],
        "weekly_hrs": 30, "burnout": 0.15, "goal_prob": 0.90,
        "status": "On Track", "alert": None,
        "student_code": "1000000000000001",
    },
    {
        "name": "Fatima Noor", "email": "fatima.noor@student.edu",
        "dept": "Computer Science", "class_lvl": "2", "section": "B",
        "cgpa": 3.20, "target": 3.7, "semester": 4, "credits": 48,
        "career_idx": 1, "gpa_trend": [3.1, 3.0, 3.2, 3.2],
        "skills": [("Machine Learning", 65, 0.45), ("Statistics", 60, 0.50), ("Python", 72, 0.30)],
        "weekly_hrs": 22, "burnout": 0.40, "goal_prob": 0.60,
        "status": "Needs Attention",
        "alert": ("performance", "medium", "GPA dropped below target — needs academic support"),
        "student_code": "1000000000000002",
    },
    {
        "name": "Khalid Mansour", "email": "khalid.mansour@student.edu",
        "dept": "Engineering", "class_lvl": "4", "section": "A",
        "cgpa": 2.10, "target": 2.5, "semester": 7, "credits": 90,
        "career_idx": 2, "gpa_trend": [2.5, 2.3, 2.1, 2.1],
        "skills": [("Problem Solving", 45, 0.75), ("Critical Thinking", 40, 0.80), ("Communication", 50, 0.65)],
        "weekly_hrs": 12, "burnout": 0.75, "goal_prob": 0.25,
        "status": "At Risk",
        "alert": ("performance", "high", "Critically low CGPA — at risk of academic probation"),
        "student_code": "1000000000000003",
    },
    {
        "name": "Sara Hussain", "email": "sara.hussain@student.edu",
        "dept": "Business", "class_lvl": "1", "section": "C",
        "cgpa": 3.60, "target": 3.8, "semester": 2, "credits": 24,
        "career_idx": 3, "gpa_trend": [3.5, 3.6],
        "skills": [("Communication", 85, 0.15), ("Project Management", 70, 0.35), ("Teamwork", 88, 0.12)],
        "weekly_hrs": 25, "burnout": 0.20, "goal_prob": 0.82,
        "status": "On Track", "alert": None,
        "student_code": "1000000000000004",
    },
    {
        "name": "Omar Qureshi", "email": "omar.qureshi@student.edu",
        "dept": "Computer Science", "class_lvl": "3", "section": "A",
        "cgpa": 1.85, "target": 2.5, "semester": 5, "credits": 60,
        "career_idx": 5, "gpa_trend": [2.2, 2.0, 1.9, 1.85],
        "skills": [("Algorithm Design", 30, 0.90), ("Web Development", 35, 0.85), ("SQL", 40, 0.80)],
        "weekly_hrs": 8, "burnout": 0.88, "goal_prob": 0.15,
        "status": "Critical",
        "alert": ("attendance", "high", "Missed 30%+ of classes this semester"),
        "student_code": "1000000000000005",
    },
    {
        "name": "Layla Ibrahim", "email": "layla.ibrahim@student.edu",
        "dept": "Computer Science", "class_lvl": "2", "section": "B",
        "cgpa": 3.90, "target": 4.0, "semester": 3, "credits": 36,
        "career_idx": 7, "gpa_trend": [3.8, 3.85, 3.9],
        "skills": [("Machine Learning", 92, 0.05), ("Python", 95, 0.05), ("Data Analysis", 88, 0.10)],
        "weekly_hrs": 35, "burnout": 0.22, "goal_prob": 0.95,
        "status": "Excellent", "alert": None,
        "student_code": "1000000000000006",
    },
    {
        "name": "Yusuf Al-Amiri", "email": "yusuf.alamiri@student.edu",
        "dept": "Business", "class_lvl": "4", "section": "A",
        "cgpa": 2.70, "target": 3.0, "semester": 7, "credits": 84,
        "career_idx": 6, "gpa_trend": [2.8, 2.7, 2.6, 2.7],
        "skills": [("Communication", 75, 0.30), ("Project Management", 68, 0.40), ("Teamwork", 80, 0.22)],
        "weekly_hrs": 18, "burnout": 0.50, "goal_prob": 0.55,
        "status": "Needs Attention",
        "alert": ("performance", "medium", "GPA trending downward over last 3 semesters"),
        "student_code": "1000000000000007",
    },
    {
        "name": "Nadia Hassan", "email": "nadia.hassan@student.edu",
        "dept": "Engineering", "class_lvl": "1", "section": "D",
        "cgpa": 3.45, "target": 3.7, "semester": 2, "credits": 24,
        "career_idx": 2, "gpa_trend": [3.4, 3.45],
        "skills": [("Problem Solving", 78, 0.22), ("Critical Thinking", 75, 0.25), ("Communication", 72, 0.28)],
        "weekly_hrs": 27, "burnout": 0.30, "goal_prob": 0.72,
        "status": "On Track", "alert": None,
        "student_code": "1000000000000008",
    },
]

# Skill catalog split by department (from seed_skills_by_dept.py)
UNIVERSAL_SKILLS = [
    "Communication", "Problem Solving", "Critical Thinking",
    "Time Management", "Teamwork", "Research", "Presentation",
    "Project Management", "Leadership", "Microsoft Office",
]
DEPT_SKILLS = {
    "Computer Science": [
        "Python", "Java", "C++", "JavaScript", "SQL", "HTML/CSS", "React",
        "Node.js", "Git", "Docker", "Linux", "Data Structures", "Algorithms",
        "Machine Learning", "Data Analysis", "Cloud Computing", "Web Development",
        "Cybersecurity", "REST APIs", "Databases",
    ],
    "Electrical Engineering": [
        "Circuit Analysis", "MATLAB", "Control Systems", "Embedded Systems",
        "Arduino", "Signal Processing", "Power Systems", "PCB Design",
        "PLC Programming", "AutoCAD Electrical", "VHDL", "Microcontrollers",
    ],
    "Mechanical Engineering": [
        "AutoCAD", "SolidWorks", "ANSYS", "Thermodynamics", "Fluid Mechanics",
        "CNC Machining", "MATLAB", "3D Modeling", "Materials Science",
        "Manufacturing Processes", "FEA Analysis", "Robot Programming",
    ],
    "Business Administration": [
        "Financial Analysis", "Accounting", "Marketing", "Sales", "Business Strategy",
        "Supply Chain", "Excel Advanced", "Business Communication", "Economics",
        "Market Research", "SAP ERP", "Digital Marketing",
    ],
    "Civil Engineering": [
        "AutoCAD Civil", "Structural Analysis", "Revit", "Surveying", "GIS",
        "Concrete Design", "Project Scheduling", "Construction Management",
        "Geotechnical Analysis", "ETABS", "Highway Design", "Environmental Engineering",
    ],
    "Medicine": [
        "Clinical Skills", "Anatomy", "Pharmacology", "Pathology", "Patient Care",
        "Medical Ethics", "Biochemistry", "Radiology Basics", "EMR Systems",
        "First Aid", "Physiology",
    ],
    "Data Science": [
        "Python", "R", "SQL", "Machine Learning", "Deep Learning", "Statistics",
        "Data Visualization", "Pandas", "NumPy", "TensorFlow", "Power BI",
        "Tableau", "Spark", "NLP",
    ],
    "Information Technology": [
        "Networking", "Cybersecurity", "Windows Server", "Linux", "Cloud Computing",
        "Virtualization", "IT Support", "Database Administration", "Active Directory",
        "Cisco Networking", "Python", "PowerShell",
    ],
    "Finance": [
        "Financial Modelling", "Accounting", "Bloomberg Terminal", "Investment Analysis",
        "Risk Management", "Excel Advanced", "Corporate Finance", "Derivatives",
        "Portfolio Management", "Financial Reporting", "QuickBooks",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def grade_from_gp(gp):
    if gp >= 3.7: return "A"
    if gp >= 3.3: return "A-"
    if gp >= 3.0: return "B+"
    if gp >= 2.7: return "B"
    if gp >= 2.3: return "B-"
    if gp >= 2.0: return "C+"
    if gp >= 1.7: return "C"
    return "D"


# ─────────────────────────────────────────────────────────────────────────────
#  Section 1: 8 demo students with full academic data
# ─────────────────────────────────────────────────────────────────────────────

def seed_students():
    print("\n" + "=" * 58)
    print("  SECTION: Demo Students (8 profiles)")
    print("=" * 58)

    # Ensure courses
    print("[1/4] Seeding CourseCatalog...")
    course_objects = {}
    for name, dept, ctype, credits in COURSES:
        existing = CourseCatalog.query.filter_by(course_name=name).first()
        if not existing:
            c = CourseCatalog(course_name=name, department=dept,
                              course_type=ctype, credit_value=credits)
            db.session.add(c)
            db.session.flush()
            course_objects[name] = c
        else:
            course_objects[name] = existing
    db.session.commit()
    print(f"   ✓ {len(course_objects)} courses ready")

    # Ensure career paths
    print("[2/4] Seeding CareerPaths...")
    career_objects = []
    for title, field in CAREERS:
        existing = CareerPath.query.filter_by(title=title).first()
        if not existing:
            cp = CareerPath(title=title, field_category=field,
                            description=f"Career path for {title} professionals.")
            db.session.add(cp)
            db.session.flush()
            career_objects.append(cp)
        else:
            career_objects.append(existing)
    db.session.commit()
    print(f"   ✓ {len(career_objects)} career paths ready")

    # Create students
    print("[3/4] Creating students...")
    created = skipped = 0
    all_course_names = list(course_objects.keys())

    for s in STUDENTS:
        if User.query.filter_by(email=s["email"]).first():
            print(f"   ↷  {s['name']} — already exists, skipping")
            skipped += 1
            continue

        user = User(email=s["email"],
                    password_hash=generate_password_hash("12345"),
                    role="student")
        db.session.add(user)
        db.session.flush()

        profile = StudentProfile(
            user_id=user.id, full_name=s["name"], department=s["dept"],
            class_level=s["class_lvl"], section=s["section"],
            current_cgpa=s["cgpa"], target_cgpa=s["target"],
            current_semester=s["semester"], completed_credits=s["credits"],
            grading_scale=4.0,
            student_code=s["student_code"],
            last_activity=datetime.utcnow() - timedelta(days=random.randint(0, 7)),
        )
        db.session.add(profile)
        db.session.flush()

        metric = AcademicMetric(
            student_id=profile.id,
            total_credits=s["credits"],
            department_rank=random.randint(1, 30),
        )
        metric.set_gpas(s["gpa_trend"])
        db.session.add(metric)

        chosen = random.sample(all_course_names, min(len(s["gpa_trend"]) * 3, len(all_course_names)))
        for sem_idx, sem_gpa in enumerate(s["gpa_trend"], start=1):
            for cname in chosen[(sem_idx - 1) * 3: sem_idx * 3]:
                gp = round(max(0, min(4.0, sem_gpa + random.uniform(-0.3, 0.3))), 1)
                db.session.add(StudentAcademicRecord(
                    student_id=profile.id,
                    course_id=course_objects[cname].id,
                    grade=grade_from_gp(gp), grade_point=gp,
                    confidence_score=random.randint(2, 5),
                    semester_taken=sem_idx,
                ))

        for skill_name, proficiency, risk in s["skills"]:
            db.session.add(StudentSkill(
                student_id=profile.id, skill_name=skill_name,
                proficiency_score=proficiency, risk_score=risk,
                last_updated=datetime.utcnow(),
            ))

        for w in range(4):
            week_date = date.today() - timedelta(weeks=w + 1)
            db.session.add(WeeklyUpdate(
                student_id=profile.id, week_start_date=week_date,
                total_hours_studied=round(max(0, s["weekly_hrs"] + random.uniform(-4, 4)), 1),
                productivity_rating=random.randint(2, 5),
                difficulty_rating=random.choice(["Easy", "Medium", "Hard"]),
                consistency_score=round(random.uniform(0.4, 1.0), 2),
                burnout_risk_score=round(min(1.0, max(0.0, s["burnout"] + random.uniform(-0.1, 0.1))), 2),
                goal_achievability_prob=round(s["goal_prob"] + random.uniform(-0.05, 0.05), 2),
                status_label=s["status"], mood_score=random.randint(2, 5),
            ))

        skills_list = [sk[0] for sk in s["skills"]]
        for d_offset in range(14):
            if random.random() > 0.3:
                db.session.add(StudySession(
                    student_id=profile.id,
                    date=date.today() - timedelta(days=d_offset),
                    duration_minutes=random.randint(30, 150),
                    topic_studied=random.choice(skills_list),
                    related_skill=random.choice(skills_list),
                ))

        career = career_objects[s["career_idx"]]
        db.session.add(StudentGoal(
            student_id=profile.id, career_id=career.id,
            goal_type="Long Term", reason=random.choice(["Interest", "Financial", "Growth"]),
            is_primary=True,
        ))

        if s["alert"]:
            atype, severity, msg = s["alert"]
            db.session.add(StudentAlert(
                student_id=profile.id, type=atype, severity=severity,
                message=msg, is_resolved=False,
            ))

        db.session.commit()
        print(f"   ✓  {s['name']} — CGPA {s['cgpa']} ({profile.performance_status})")
        created += 1

    print(f"\n[4/4] Done — Created: {created}  Skipped: {skipped}")
    print("   Password for all students: 12345")


# ─────────────────────────────────────────────────────────────────────────────
#  Section 2: Teacher + 7 students (for teacher-dashboard testing)
# ─────────────────────────────────────────────────────────────────────────────

def seed_teacher():
    print("\n" + "=" * 58)
    print("  SECTION: Teacher + Classroom Data")
    print("=" * 58)

    TEACHER_EMAIL = "teacher@test.com"
    TEACHER_PASS  = "Teacher@123"

    # Teacher
    t_user = User.query.filter_by(email=TEACHER_EMAIL).first()
    if not t_user:
        t_user = User(email=TEACHER_EMAIL,
                      password_hash=generate_password_hash(TEACHER_PASS),
                      role="teacher")
        db.session.add(t_user)
        db.session.flush()
        teacher = TeacherProfile(user_id=t_user.id, full_name="Dr. Sarah Johnson",
                                 department="Mathematics",
                                 subject_specialization="Algebra & Calculus")
        db.session.add(teacher)
        db.session.commit()
        print(f"   ✓ Teacher created: {TEACHER_EMAIL} / {TEACHER_PASS}")
    else:
        teacher = TeacherProfile.query.filter_by(user_id=t_user.id).first()
        print(f"   ↷ Teacher already exists — skipping creation")

    CLASSROOM = [
        {"name": "Alice Smith",    "class": "10", "section": "A", "cgpa": 3.8, "student_code": "2000000000000001"},
        {"name": "Bob Jones",      "class": "10", "section": "A", "cgpa": 2.9, "student_code": "2000000000000002"},
        {"name": "Charlie Brown",  "class": "10", "section": "A", "cgpa": 2.1, "student_code": "2000000000000003"},
        {"name": "Diana Prince",   "class": "10", "section": "B", "cgpa": 3.9, "student_code": "2000000000000004"},
        {"name": "Eve Wilson",     "class": "10", "section": "B", "cgpa": 1.8, "student_code": "2000000000000005"},
        {"name": "Frank Miller",   "class": "9",  "section": "A", "cgpa": 3.2, "student_code": "2000000000000006"},
        {"name": "Grace Hopper",   "class": "9",  "section": "A", "cgpa": 4.0, "student_code": "2000000000000007"},
    ]

    student_objs = []
    for s_data in CLASSROOM:
        email = f"{s_data['name'].lower().replace(' ', '.')}@student.com"
        if User.query.filter_by(email=email).first():
            print(f"   ↷ {s_data['name']} already exists")
            p = StudentProfile.query.join(User).filter(User.email == email).first()
            if p:
                student_objs.append(p)
            continue

        u = User(email=email, password_hash=generate_password_hash("12345"), role="student")
        db.session.add(u)
        db.session.flush()

        p = StudentProfile(
            user_id=u.id, full_name=s_data["name"],
            class_level=s_data["class"], section=s_data["section"],
            current_cgpa=s_data["cgpa"], department="General",
            student_code=s_data["student_code"],
            last_activity=datetime.utcnow() - timedelta(hours=random.randint(1, 48)),
        )
        db.session.add(p)
        db.session.flush()

        TeacherAssignment.query.filter_by(teacher_id=teacher.id, student_id=p.id).first() or \
            db.session.add(TeacherAssignment(
                teacher_id=teacher.id, student_id=p.id,
                class_level=s_data["class"], section=s_data["section"],
                subject="Mathematics", assignment_type="subject",
            ))

        gpas = [3.0, 3.2, 3.1, 3.4, 3.8] if s_data["cgpa"] >= 2.5 else [3.0, 2.8, 2.5, 2.2, 2.1]
        metric = AcademicMetric(student_id=p.id, total_credits=45,
                                department_rank=random.randint(1, 100),
                                semester_gpas=json.dumps(gpas))
        db.session.add(metric)
        db.session.add(StudentSkill(student_id=p.id, skill_name="Python", proficiency_score=60))
        db.session.add(CareerInterest(student_id=p.id, field_name="Data Science", interest_score=85.0))
        db.session.add(AnalyticsResult(
            student_id=p.id, predicted_next_gpa=s_data["cgpa"],
            career_predictions='{"Data Scientist": 85, "Software Engineer": 75}',
            skill_recommendations='["SQL", "Machine Learning"]',
        ))
        db.session.commit()
        student_objs.append(p)
        print(f"   ✓ {s_data['name']} (CGPA {s_data['cgpa']})")

    # Attendance: last 30 days
    print("   → Generating attendance records...")
    for s_obj in student_objs:
        if Attendance.query.filter_by(student_id=s_obj.id).first():
            continue
        for i in range(30):
            d = datetime.utcnow().date() - timedelta(days=i)
            weights = [60, 30, 10] if (s_obj.current_cgpa or 2.0) < 2.5 else [90, 5, 5]
            status = random.choices(["present", "absent", "late"], weights=weights)[0]
            db.session.add(Attendance(student_id=s_obj.id, date=d, status=status))
    db.session.commit()

    # Assignments + submissions
    print("   → Creating assignments & submissions...")
    assignments_data = [
        {"title": "Algebra Quiz 1",        "points": 20,  "days_ago": 15},
        {"title": "Mid-term Project",       "points": 100, "days_ago": 10},
        {"title": "Trigonometry Worksheet", "points": 50,  "days_ago": 5},
    ]
    assignment_objs = []
    for a in assignments_data:
        existing = Assignment.query.filter_by(title=a["title"], teacher_id=teacher.id).first()
        if existing:
            assignment_objs.append(existing)
            continue
        obj = Assignment(
            title=a["title"], subject="Mathematics", teacher_id=teacher.id,
            total_points=a["points"],
            due_date=(datetime.utcnow() - timedelta(days=a["days_ago"] - 2)).date(),
            created_at=datetime.utcnow() - timedelta(days=a["days_ago"]),
        )
        db.session.add(obj)
        db.session.flush()
        assignment_objs.append(obj)
    db.session.commit()

    for s_obj in student_objs:
        for a_obj in assignment_objs:
            if AssignmentSubmission.query.filter_by(assignment_id=a_obj.id, student_id=s_obj.id).first():
                continue
            cgpa = s_obj.current_cgpa or 2.0
            if cgpa < 2.5 and random.random() < 0.3:
                continue
            score = int(a_obj.total_points * (cgpa / 4.0) * random.uniform(0.8, 1.0))
            status = "late" if random.random() < 0.1 else "submitted"
            db.session.add(AssignmentSubmission(
                assignment_id=a_obj.id, student_id=s_obj.id,
                score=score, submitted_at=datetime.utcnow(), status=status,
            ))
    db.session.commit()

    # Notes & alerts for at-risk students
    print("   → Adding notes & alerts...")
    for s_obj in student_objs:
        if (s_obj.current_cgpa or 0) < 2.5:
            if not StudentNote.query.filter_by(student_id=s_obj.id, teacher_id=teacher.id).first():
                db.session.add(StudentNote(
                    student_id=s_obj.id, teacher_id=teacher.id,
                    content=f"{s_obj.full_name} struggling with Algebra — schedule extra help.",
                    is_private=True,
                ))
            if not StudentAlert.query.filter_by(student_id=s_obj.id, type="performance").first():
                db.session.add(StudentAlert(
                    student_id=s_obj.id, type="performance", severity="high",
                    message="CGPA dropped below 2.5 threshold.", is_resolved=False,
                ))
    db.session.commit()
    print("   ✓ Teacher section done")


# ─────────────────────────────────────────────────────────────────────────────
#  Section 3: Skill catalog (Skill master table by department)
# ─────────────────────────────────────────────────────────────────────────────

def seed_skills_catalog():
    print("\n" + "=" * 58)
    print("  SECTION: Skill Catalog (department-tagged)")
    print("=" * 58)

    try:
        from models import Skill
    except ImportError:
        print("   ✗ Skill model not found — skipping")
        return

    all_to_seed = [(name, None) for name in UNIVERSAL_SKILLS]
    for dept, skills in DEPT_SKILLS.items():
        for name in skills:
            all_to_seed.append((name, dept))

    updated = added = 0
    for skill_name, department in all_to_seed:
        existing = Skill.query.filter(
            db.func.lower(Skill.skill_name) == skill_name.lower()
        ).first()
        if existing:
            existing.department = department
            updated += 1
        else:
            db.session.add(Skill(skill_name=skill_name, department=department))
            added += 1

    db.session.commit()
    print(f"   ✓ Updated: {updated}  Added: {added}  "
          f"(Departments: {', '.join(DEPT_SKILLS.keys())})")


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Student Insight System — Unified Seed Script"
    )
    parser.add_argument("--students",       action="store_true", help="Seed 8 demo students")
    parser.add_argument("--teacher",        action="store_true", help="Seed teacher + classroom data")
    parser.add_argument("--skills-catalog", action="store_true", help="Seed the Skill catalog by department")
    args = parser.parse_args()

    # If no flags given, run everything
    run_all = not any([args.students, args.teacher, args.skills_catalog])

    with app.app_context():
        if run_all or args.students:
            seed_students()
        if run_all or args.teacher:
            seed_teacher()
        if run_all or args.skills_catalog:
            seed_skills_catalog()

    print("\n✅ Seeding complete.\n")


if __name__ == "__main__":
    main()
