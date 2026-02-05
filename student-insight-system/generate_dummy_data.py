import random
import json
from app import app, db
from models import StudentProfile, AcademicMetric, StudentSkill, StudentCourse, CareerInterest

def generate_dummy_data():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()

        departments = ['Computer Science', 'Software Engineering', 'Information Technology', 'Data Science']
        skills_pool = ['Python', 'Java', 'C++', 'JavaScript', 'React', 'Node.js', 'SQL', 'Machine Learning', 'AWS', 'Docker', 'Kubernetes', 'Cybersecurity', 'Data Analysis']
        courses_pool = ['Data Structures', 'Algorithms', 'Database Systems', 'Operating Systems', 'Computer Networks', 'Software Engineering', 'Web Development', 'Artificial Intelligence', 'Calculus', 'Linear Algebra']
        career_fields = ['Software Development', 'Data Science', 'AI/ML', 'Cloud Computing', 'Cybersecurity', 'DevOps', 'Product Management']

        students = []
        for i in range(20):
            # Create Profile
            profile = StudentProfile(
                full_name=f"Student {i+1}",
                email=f"student{i+1}@example.com",
                department=random.choice(departments),
                current_cgpa=round(random.uniform(2.5, 4.0), 2)
            )
            db.session.add(profile)
            db.session.flush() # Get ID

            # Academic Metrics
            gpas = [round(random.uniform(2.5, 4.0), 2) for _ in range(6)]
            metric = AcademicMetric(
                student_id=profile.id,
                semester_gpas=json.dumps(gpas),
                total_credits=random.randint(80, 110),
                department_rank=random.randint(1, 150)
            )
            db.session.add(metric)

            # Skills
            num_skills = random.randint(3, 8)
            student_skills = random.sample(skills_pool, num_skills)
            for skill in student_skills:
                db.session.add(StudentSkill(
                    student_id=profile.id,
                    skill_name=skill,
                    proficiency_level=random.choice(['Beginner', 'Intermediate', 'Advanced'])
                ))

            # Courses
            num_courses = random.randint(4, 6)
            student_courses = random.sample(courses_pool, num_courses)
            for course in student_courses:
                course_type = random.choice(['strong', 'weak'])
                grade = 'A' if course_type == 'strong' else random.choice(['B-', 'C+', 'C'])
                db.session.add(StudentCourse(
                    student_id=profile.id,
                    course_name=course,
                    course_type=course_type,
                    grade=grade
                ))

            # Career Interests (Random initial data)
            num_interests = random.randint(3, 5)
            student_interests = random.sample(career_fields, num_interests)
            for field in student_interests:
                db.session.add(CareerInterest(
                    student_id=profile.id,
                    field_name=field,
                    interest_score=round(random.uniform(50, 100), 1)
                ))

        db.session.commit()
        print("Dummy data generated successfully!")

if __name__ == "__main__":
    generate_dummy_data()
