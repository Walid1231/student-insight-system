"""
Seed 20 new student users with a FULL YEAR of balanced, realistic data.
Each student sees their own data on the dashboard.

Usage:  python seed_20_students.py
"""
import sys, os, random, json
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import (
    db, User, StudentProfile, AcademicMetric, StudentSkill,
    CareerInterest, StudentCourse, AnalyticsResult,
    CourseCatalog, Skill, CareerPath, CareerRequiredSkill,
    StudentAcademicRecord, StudySession, WeeklyUpdate, StudentGoal
)
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta, date

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
NUM_STUDENTS = 20
PASSWORD = "password123"
YEAR_START = date(2025, 3, 1)   # data spans Mar 2025 → Feb 2026
WEEKS_IN_YEAR = 52

# 20 realistic names
NAMES = [
    "Arif Rahman", "Nusrat Jahan", "Tanvir Ahmed", "Fatima Khatun",
    "Sakib Hossain", "Maliha Tasnim", "Rahat Islam", "Sumaiya Akter",
    "Imran Khan", "Nafisa Nahar", "Fahim Shahriar", "Tasnia Rahman",
    "Jubayer Hasan", "Rima Sultana", "Siam Reza", "Lamia Akhtar",
    "Mehedi Hasan", "Jannatul Ferdous", "Ashraf Uddin", "Nadia Islam"
]

DEPARTMENTS = ["Computer Science", "Software Engineering", "Information Technology", "Data Science"]
SECTIONS = ["A", "B", "C"]
CLASS_LEVELS = ["9", "10", "11", "12"]

# 4 archetypes (5 students each)
ARCHETYPES = {
    "high_performer": {
        "cgpa_range": (3.50, 3.95),
        "gpa_base": 3.50,
        "gpa_trend": "up",       # generally improving
        "skill_range": (70, 95),
        "study_hrs_range": (2.0, 5.0),
        "burnout_range": (0.10, 0.40),
        "goal_prob_range": (0.75, 0.95),
    },
    "steady_improver": {
        "cgpa_range": (3.00, 3.50),
        "gpa_base": 2.80,
        "gpa_trend": "up",
        "skill_range": (50, 80),
        "study_hrs_range": (1.5, 4.0),
        "burnout_range": (0.25, 0.55),
        "goal_prob_range": (0.60, 0.85),
    },
    "average": {
        "cgpa_range": (2.70, 3.20),
        "gpa_base": 2.80,
        "gpa_trend": "flat",
        "skill_range": (40, 70),
        "study_hrs_range": (1.0, 3.0),
        "burnout_range": (0.30, 0.60),
        "goal_prob_range": (0.50, 0.75),
    },
    "struggling": {
        "cgpa_range": (2.00, 2.80),
        "gpa_base": 2.30,
        "gpa_trend": "down",
        "skill_range": (20, 55),
        "study_hrs_range": (0.5, 2.0),
        "burnout_range": (0.55, 0.85),
        "goal_prob_range": (0.30, 0.55),
    },
}

SKILL_NAMES_POOL = [
    "Python", "Java", "SQL", "JavaScript", "HTML/CSS",
    "Data Analysis", "Machine Learning", "Communication",
    "Problem Solving", "Web Development", "Cloud Computing",
    "Git", "Linux", "Docker", "React"
]

CAREER_POOL = [
    "Software Engineer", "Data Scientist", "Web Developer",
    "Machine Learning Engineer", "DevOps Engineer", "Database Administrator"
]

GRADE_MAP = [
    ("A",  4.0), ("A-", 3.7), ("B+", 3.3), ("B", 3.0),
    ("B-", 2.7), ("C+", 2.3), ("C",  2.0), ("D",  1.0)
]


def _gen_semester_gpas(archetype, n=6):
    """Generate n semester GPAs following archetype pattern."""
    a = ARCHETYPES[archetype]
    base = a["gpa_base"]
    gpas = []
    for i in range(n):
        if a["gpa_trend"] == "up":
            g = base + i * random.uniform(0.05, 0.15)
        elif a["gpa_trend"] == "down":
            g = base - i * random.uniform(0.03, 0.10)
        else:  # flat
            g = base + random.uniform(-0.10, 0.10)
        g = round(min(4.0, max(1.0, g + random.uniform(-0.08, 0.08))), 2)
        gpas.append(g)
    return gpas


def _pick_grades_for_archetype(archetype, n):
    """Pick n grade tuples weighted by archetype."""
    a = ARCHETYPES[archetype]
    lo, hi = a["skill_range"]
    grades = []
    for _ in range(n):
        # Higher skill → better grades
        level = random.uniform(lo, hi) / 100.0
        idx = max(0, min(len(GRADE_MAP) - 1, int((1 - level) * len(GRADE_MAP))))
        idx = max(0, min(len(GRADE_MAP) - 1, idx + random.randint(-1, 1)))
        grades.append(GRADE_MAP[idx])
    return grades


def ensure_master_data():
    """Create shared catalog/skill/career data if not present."""
    # --- Course Catalog ---
    if CourseCatalog.query.count() == 0:
        print("  Creating CourseCatalog...")
        courses = [
            ("Programming Fundamentals", "Computer Science", "Core", 3),
            ("Data Structures", "Computer Science", "Core", 3),
            ("Database Systems", "Computer Science", "Core", 3),
            ("Operating Systems", "Computer Science", "Core", 3),
            ("Computer Networks", "Computer Science", "Core", 3),
            ("Software Engineering", "Computer Science", "Core", 3),
            ("Algorithms", "Computer Science", "Core", 3),
            ("Web Development", "Computer Science", "Core", 3),
            ("Discrete Mathematics", "Mathematics", "Core", 3),
            ("Linear Algebra", "Mathematics", "Core", 3),
            ("English Composition", "General", "GED", 3),
            ("Public Speaking", "General", "GED", 3),
            ("Introduction to Psychology", "General", "GED", 3),
            ("Art Appreciation", "General", "GED", 2),
            ("Environmental Science", "General", "GED", 3),
            ("World History", "General", "GED", 3),
            ("Machine Learning", "Computer Science", "Elective", 3),
            ("Cloud Computing", "Computer Science", "Elective", 3),
        ]
        for name, dept, ctype, cr in courses:
            db.session.add(CourseCatalog(course_name=name, department=dept,
                                         course_type=ctype, credit_value=cr))
        db.session.flush()

    # --- Skills master ---
    if Skill.query.count() == 0:
        print("  Creating Skills...")
        for sn in SKILL_NAMES_POOL:
            db.session.add(Skill(skill_name=sn))
        db.session.flush()

    # --- Career Paths ---
    if CareerPath.query.count() == 0:
        print("  Creating CareerPaths...")
        careers = [
            ("Software Engineer", "IT", "Designs, develops, and maintains software systems."),
            ("Data Scientist", "Data Science", "Analyzes complex data to help businesses."),
            ("Web Developer", "IT", "Builds and maintains websites."),
            ("Machine Learning Engineer", "AI", "Builds and deploys ML models."),
            ("DevOps Engineer", "IT", "Manages CI/CD and cloud infrastructure."),
            ("Database Administrator", "IT", "Manages and optimizes databases."),
        ]
        for title, field, desc in careers:
            db.session.add(CareerPath(title=title, field_category=field, description=desc))
        db.session.flush()

    # --- Career Required Skills ---
    if CareerRequiredSkill.query.count() == 0:
        print("  Creating CareerRequiredSkills...")
        all_careers = {c.title: c.id for c in CareerPath.query.all()}
        all_skills = {s.skill_name: s.id for s in Skill.query.all()}
        mapping = {
            "Software Engineer": [("Python", "High"), ("Java", "High"), ("Git", "High"), ("SQL", "Medium"), ("Problem Solving", "High")],
            "Data Scientist": [("Python", "High"), ("SQL", "High"), ("Machine Learning", "High"), ("Data Analysis", "High"), ("Communication", "Medium")],
            "Web Developer": [("JavaScript", "High"), ("HTML/CSS", "High"), ("React", "High"), ("Git", "Medium"), ("Web Development", "High")],
            "Machine Learning Engineer": [("Python", "High"), ("Machine Learning", "High"), ("Data Analysis", "High"), ("Docker", "Medium"), ("Linux", "Medium")],
            "DevOps Engineer": [("Docker", "High"), ("Linux", "High"), ("Cloud Computing", "High"), ("Git", "High"), ("Python", "Medium")],
            "Database Administrator": [("SQL", "High"), ("Linux", "Medium"), ("Python", "Medium"), ("Cloud Computing", "Medium"), ("Problem Solving", "High")],
        }
        for career_title, skills in mapping.items():
            if career_title not in all_careers:
                continue
            for skill_name, importance in skills:
                if skill_name in all_skills:
                    db.session.add(CareerRequiredSkill(
                        career_id=all_careers[career_title],
                        skill_id=all_skills[skill_name],
                        importance_level=importance
                    ))
        db.session.flush()


def seed():
    with app.app_context():
        # Check idempotency
        existing = User.query.filter_by(email="student1@test.com").first()
        if existing:
            print("Seed users already exist. Deleting old seed data and re-creating...")
            for i in range(1, NUM_STUDENTS + 1):
                u = User.query.filter_by(email=f"student{i}@test.com").first()
                if u:
                    db.session.delete(u)  # cascade deletes profile + related
            db.session.commit()
            print("  Old seed data removed.")

        ensure_master_data()
        db.session.flush()

        catalog_courses = CourseCatalog.query.all()
        all_career_paths = CareerPath.query.all()
        archetype_keys = list(ARCHETYPES.keys())
        hashed_pw = generate_password_hash(PASSWORD)

        counters = {
            "users": 0, "profiles": 0, "academic_metrics": 0,
            "skills": 0, "career_interests": 0, "academic_records": 0,
            "study_sessions": 0, "weekly_updates": 0, "goals": 0
        }

        for idx in range(NUM_STUDENTS):
            i = idx + 1
            archetype = archetype_keys[idx % len(archetype_keys)]
            a = ARCHETYPES[archetype]

            # --- 1. User ---
            user = User(
                email=f"student{i}@test.com",
                password_hash=hashed_pw,
                role="student"
            )
            db.session.add(user)
            db.session.flush()
            counters["users"] += 1

            # --- 2. StudentProfile ---
            semester_gpas = _gen_semester_gpas(archetype, 6)
            current_cgpa = round(sum(semester_gpas) / len(semester_gpas), 2)

            profile = StudentProfile(
                user_id=user.id,
                full_name=NAMES[idx],
                department=random.choice(DEPARTMENTS),
                class_level=random.choice(CLASS_LEVELS),
                section=random.choice(SECTIONS),
                current_cgpa=current_cgpa,
                current_semester=6,
                grading_scale=4.0,
                completed_credits=random.randint(60, 100),
            )
            db.session.add(profile)
            db.session.flush()
            counters["profiles"] += 1

            # --- 3. AcademicMetric ---
            am = AcademicMetric(
                student_id=profile.id,
                semester_gpas=json.dumps(semester_gpas),
                total_credits=profile.completed_credits,
                department_rank=random.randint(1, 60)
            )
            db.session.add(am)
            counters["academic_metrics"] += 1

            # --- 4. StudentSkill (6 per student) ---
            chosen_skills = random.sample(SKILL_NAMES_POOL, 6)
            lo, hi = a["skill_range"]
            for skill_name in chosen_skills:
                db.session.add(StudentSkill(
                    student_id=profile.id,
                    skill_name=skill_name,
                    proficiency_score=random.randint(lo, hi),
                    risk_score=round(random.uniform(0.0, 1.0 - lo / 100), 2),
                    last_updated=datetime.utcnow()
                ))
                counters["skills"] += 1

            # --- 5. CareerInterest (3 per student) ---
            chosen_careers = random.sample(CAREER_POOL, 3)
            for career_name in chosen_careers:
                db.session.add(CareerInterest(
                    student_id=profile.id,
                    field_name=career_name,
                    interest_score=random.randint(55, 95)
                ))
                counters["career_interests"] += 1

            # --- 6. StudentAcademicRecord (8-12 courses) ---
            n_courses = random.randint(8, min(12, len(catalog_courses)))
            chosen_courses = random.sample(catalog_courses, n_courses)
            grades = _pick_grades_for_archetype(archetype, n_courses)
            for ci, (grade_str, grade_pt) in zip(chosen_courses, grades):
                db.session.add(StudentAcademicRecord(
                    student_id=profile.id,
                    course_id=ci.id,
                    grade=grade_str,
                    grade_point=grade_pt,
                    confidence_score=random.randint(2, 5),
                    semester_taken=random.randint(1, 6)
                ))
                counters["academic_records"] += 1

            # --- 7. StudySession (~365 entries, 1 year) ---
            study_lo, study_hi = a["study_hrs_range"]
            skill_topics = chosen_skills  # use same skills for study sessions
            for day_offset in range(365):
                session_date = YEAR_START + timedelta(days=day_offset)
                # Some days have 0 sessions (weekends less likely to study)
                weekday = session_date.weekday()
                if weekday >= 5:  # weekend
                    if random.random() < 0.4:
                        continue
                else:
                    if random.random() < 0.1:  # 10% skip on weekdays
                        continue

                skill = random.choice(skill_topics)
                duration = int(random.uniform(study_lo, study_hi) * 60)
                db.session.add(StudySession(
                    student_id=profile.id,
                    date=session_date,
                    duration_minutes=max(15, duration),
                    topic_studied=f"Studying {skill}",
                    related_skill=skill
                ))
                counters["study_sessions"] += 1

            # --- 8. WeeklyUpdate (52 weeks) ---
            burnout_lo, burnout_hi = a["burnout_range"]
            goal_lo, goal_hi = a["goal_prob_range"]
            for week_num in range(WEEKS_IN_YEAR):
                week_start = YEAR_START + timedelta(weeks=week_num)
                # Add slight trend noise
                burnout = round(random.uniform(burnout_lo, burnout_hi) +
                                random.uniform(-0.05, 0.05), 2)
                burnout = max(0.0, min(1.0, burnout))
                goal_p = round(random.uniform(goal_lo, goal_hi) +
                               random.uniform(-0.05, 0.05), 2)
                goal_p = max(0.0, min(1.0, goal_p))

                db.session.add(WeeklyUpdate(
                    student_id=profile.id,
                    week_start_date=week_start,
                    total_hours_studied=round(random.uniform(
                        study_lo * 5, study_hi * 7), 1),
                    productivity_rating=random.randint(2, 5),
                    difficulty_rating=random.choice(["Easy", "Medium", "Hard"]),
                    consistency_score=round(random.uniform(0.4, 0.95), 2),
                    burnout_risk_score=burnout,
                    goal_achievability_prob=goal_p,
                    status_label=random.choice(
                        ["On Track", "At Risk", "Needs Improvement", "Excellent"]
                    ),
                ))
                counters["weekly_updates"] += 1

            # --- 9. StudentGoal (1-2 career goals) ---
            if all_career_paths:
                n_goals = random.randint(1, 2)
                goal_careers = random.sample(all_career_paths,
                                             min(n_goals, len(all_career_paths)))
                for gi, career in enumerate(goal_careers):
                    db.session.add(StudentGoal(
                        student_id=profile.id,
                        career_id=career.id,
                        goal_type=random.choice(["Short Term", "Long Term"]),
                        reason=random.choice(["Interest", "Financial", "Growth"]),
                        is_primary=(gi == 0)
                    ))
                    counters["goals"] += 1

            if i % 5 == 0:
                db.session.flush()
                print(f"  [OK] Seeded student {i}/20 ({archetype})")

        db.session.commit()
        print("\n" + "=" * 55)
        print("  SEED COMPLETE — 20 students with 1 year of data")
        print("=" * 55)
        for k, v in counters.items():
            print(f"  {k:>20s}: {v}")
        print(f"\n  Login: student1@test.com / {PASSWORD}")
        print(f"         student2@test.com / {PASSWORD}")
        print(f"         ...through student20@test.com")
        print("=" * 55)


if __name__ == "__main__":
    seed()
