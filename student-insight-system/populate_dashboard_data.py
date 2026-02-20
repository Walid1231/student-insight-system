"""
Populate the database tables needed for the Student Dashboard widgets.
Tables: CourseCatalog, StudentAcademicRecord, StudySession, WeeklyUpdate,
        CareerPath, CareerRequiredSkill, StudentGoal, Skill
"""
import sys
sys.path.insert(0, '.')
from app import app
from models import *
from datetime import datetime, timedelta, date
import random

def populate():
    with app.app_context():
        students = StudentProfile.query.all()
        if not students:
            print("No students found. Aborting.")
            return

        # ---- 1. COURSE CATALOG ----
        if CourseCatalog.query.count() == 0:
            print("Populating CourseCatalog...")
            courses = [
                # Core courses
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
                # GED courses
                ("English Composition", "General", "GED", 3),
                ("Public Speaking", "General", "GED", 3),
                ("Introduction to Psychology", "General", "GED", 3),
                ("Art Appreciation", "General", "GED", 2),
                ("Environmental Science", "General", "GED", 3),
                ("World History", "General", "GED", 3),
                # Electives
                ("Machine Learning", "Computer Science", "Elective", 3),
                ("Cloud Computing", "Computer Science", "Elective", 3),
            ]
            for name, dept, ctype, credits in courses:
                db.session.add(CourseCatalog(
                    course_name=name, department=dept,
                    course_type=ctype, credit_value=credits
                ))
            db.session.flush()
            print(f"  Added {len(courses)} catalog courses.")

        # ---- 2. SKILLS (Master list) ----
        if Skill.query.count() == 0:
            print("Populating Skills master list...")
            skill_names = ["Python", "Java", "SQL", "JavaScript", "HTML/CSS",
                           "Data Analysis", "Machine Learning", "Communication",
                           "Problem Solving", "Web Development", "Cloud Computing",
                           "Git", "Linux", "Docker", "React"]
            for sn in skill_names:
                db.session.add(Skill(skill_name=sn))
            db.session.flush()
            print(f"  Added {len(skill_names)} skills.")

        # ---- 3. CAREER PATHS ----
        if CareerPath.query.count() == 0:
            print("Populating CareerPaths...")
            careers = [
                ("Software Engineer", "IT", "Designs, develops, and maintains software systems."),
                ("Data Scientist", "Data Science", "Analyzes complex data to help businesses make decisions."),
                ("Web Developer", "IT", "Builds and maintains websites and web applications."),
                ("Machine Learning Engineer", "AI", "Builds ML models and deploys them to production."),
                ("DevOps Engineer", "IT", "Manages CI/CD pipelines and cloud infrastructure."),
                ("Database Administrator", "IT", "Manages and optimizes database systems."),
            ]
            for title, field, desc in careers:
                db.session.add(CareerPath(title=title, field_category=field, description=desc))
            db.session.flush()
            print(f"  Added {len(careers)} career paths.")

        # ---- 4. CAREER REQUIRED SKILLS ----
        if CareerRequiredSkill.query.count() == 0:
            print("Populating CareerRequiredSkills...")
            all_careers = CareerPath.query.all()
            all_skills = {s.skill_name: s.id for s in Skill.query.all()}
            
            career_skills_map = {
                "Software Engineer": [("Python", "High"), ("Java", "High"), ("Git", "High"), ("SQL", "Medium"), ("Problem Solving", "High")],
                "Data Scientist": [("Python", "High"), ("SQL", "High"), ("Machine Learning", "High"), ("Data Analysis", "High"), ("Communication", "Medium")],
                "Web Developer": [("JavaScript", "High"), ("HTML/CSS", "High"), ("React", "High"), ("Git", "Medium"), ("Web Development", "High")],
                "Machine Learning Engineer": [("Python", "High"), ("Machine Learning", "High"), ("Data Analysis", "High"), ("Docker", "Medium"), ("Linux", "Medium")],
                "DevOps Engineer": [("Docker", "High"), ("Linux", "High"), ("Cloud Computing", "High"), ("Git", "High"), ("Python", "Medium")],
                "Database Administrator": [("SQL", "High"), ("Linux", "Medium"), ("Python", "Medium"), ("Cloud Computing", "Medium"), ("Problem Solving", "High")],
            }
            count = 0
            for career in all_careers:
                skills_for = career_skills_map.get(career.title, [])
                for skill_name, importance in skills_for:
                    if skill_name in all_skills:
                        db.session.add(CareerRequiredSkill(
                            career_id=career.id,
                            skill_id=all_skills[skill_name],
                            importance_level=importance
                        ))
                        count += 1
            db.session.flush()
            print(f"  Added {count} career-skill links.")

        # ---- 5. STUDENT ACADEMIC RECORDS (for Core vs GED chart) ----
        if StudentAcademicRecord.query.count() == 0:
            print("Populating StudentAcademicRecords...")
            catalog_courses = CourseCatalog.query.all()
            grades = [("A", 4.0), ("A-", 3.7), ("B+", 3.3), ("B", 3.0), ("B-", 2.7), ("C+", 2.3), ("C", 2.0)]
            count = 0
            for student in students:
                # Give each student 6-10 random courses
                n_courses = random.randint(6, min(10, len(catalog_courses)))
                chosen = random.sample(catalog_courses, n_courses)
                for i, course in enumerate(chosen):
                    grade_str, grade_pt = random.choice(grades)
                    db.session.add(StudentAcademicRecord(
                        student_id=student.id,
                        course_id=course.id,
                        grade=grade_str,
                        grade_point=grade_pt,
                        confidence_score=random.randint(2, 5),
                        semester_taken=random.randint(1, 5)
                    ))
                    count += 1
            db.session.flush()
            print(f"  Added {count} academic records.")

        # ---- 6. STUDY SESSIONS (for Weekly Study Hours & Skill Effort) ----
        if StudySession.query.count() == 0:
            print("Populating StudySessions...")
            today = date.today()
            week_start = today - timedelta(days=today.weekday())  # Monday
            skill_topics = ["Python", "SQL", "Communication", "Web Development", "Data Analysis", "Machine Learning"]
            count = 0
            for student in students:
                # Create sessions for this week and last week
                for day_offset in range(-7, 7):
                    session_date = week_start + timedelta(days=day_offset)
                    n_sessions = random.randint(0, 3)
                    for _ in range(n_sessions):
                        skill = random.choice(skill_topics)
                        db.session.add(StudySession(
                            student_id=student.id,
                            date=session_date,
                            duration_minutes=random.randint(20, 180),
                            topic_studied=f"Studying {skill}",
                            related_skill=skill
                        ))
                        count += 1
            db.session.flush()
            print(f"  Added {count} study sessions.")

        # ---- 7. WEEKLY UPDATES (for Burnout & Goal Achievability) ----
        if WeeklyUpdate.query.count() == 0:
            print("Populating WeeklyUpdates...")
            today = date.today()
            count = 0
            for student in students:
                # Create 4 weeks of updates
                for w in range(4):
                    week_start = today - timedelta(weeks=w, days=today.weekday())
                    burnout = round(random.uniform(0.2, 0.8), 2)
                    goal_prob = round(random.uniform(0.5, 0.95), 2)
                    db.session.add(WeeklyUpdate(
                        student_id=student.id,
                        week_start_date=week_start,
                        total_hours_studied=round(random.uniform(8, 35), 1),
                        productivity_rating=random.randint(2, 5),
                        difficulty_rating=random.choice(["Easy", "Medium", "Hard"]),
                        consistency_score=round(random.uniform(0.4, 0.95), 2),
                        burnout_risk_score=burnout,
                        goal_achievability_prob=goal_prob,
                        status_label=random.choice(["On Track", "At Risk", "Needs Improvement"]),
                    ))
                    count += 1
            db.session.flush()
            print(f"  Added {count} weekly updates.")

        # ---- 8. STUDENT GOALS ----
        if StudentGoal.query.count() == 0:
            print("Populating StudentGoals...")
            all_careers = CareerPath.query.all()
            count = 0
            if all_careers:
                for student in students:
                    # Each student gets 1-2 goals
                    n_goals = random.randint(1, 2)
                    chosen_careers = random.sample(all_careers, min(n_goals, len(all_careers)))
                    for i, career in enumerate(chosen_careers):
                        db.session.add(StudentGoal(
                            student_id=student.id,
                            career_id=career.id,
                            goal_type=random.choice(["Short Term", "Long Term"]),
                            reason=random.choice(["Interest", "Financial", "Growth"]),
                            is_primary=(i == 0)
                        ))
                        count += 1
            db.session.flush()
            print(f"  Added {count} student goals.")

        db.session.commit()
        print("\n=== All dashboard data populated successfully! ===")

        # Verify
        print(f"\nVerification:")
        print(f"  CourseCatalog: {CourseCatalog.query.count()}")
        print(f"  Skill: {Skill.query.count()}")
        print(f"  CareerPath: {CareerPath.query.count()}")
        print(f"  CareerRequiredSkill: {CareerRequiredSkill.query.count()}")
        print(f"  StudentAcademicRecord: {StudentAcademicRecord.query.count()}")
        print(f"  StudySession: {StudySession.query.count()}")
        print(f"  WeeklyUpdate: {WeeklyUpdate.query.count()}")
        print(f"  StudentGoal: {StudentGoal.query.count()}")

if __name__ == "__main__":
    populate()
