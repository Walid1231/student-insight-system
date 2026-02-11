
import sys
import os

# Add parent directory to path to import app and models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import StudentProfile, StudentSkill, StudentSkillProgress
from datetime import datetime, timedelta
import random

def seed_skills():
    with app.app_context():
        # Get the first student
        student = StudentProfile.query.first()
        if not student:
            print("No student found. Please register a student first.")
            return

        print(f"Seeding skills for student: {student.full_name}")

        skills_data = [
            {"name": "Python", "score": 65},
            {"name": "Data Analysis", "score": 40},
            {"name": "Web Development", "score": 85},
            {"name": "Machine Learning", "score": 30},
            {"name": "Communication", "score": 75}
        ]

        for data in skills_data:
            skill = StudentSkill.query.filter_by(student_id=student.id, skill_name=data["name"]).first()
            if not skill:
                skill = StudentSkill(student_id=student.id, skill_name=data["name"])
                db.session.add(skill)
            
            skill.proficiency_score = data["score"]
            # Calculate simple mock risk
            skill.risk_score = round(1.0 - (data["score"] / 100.0), 2)
            skill.last_updated = datetime.utcnow()
            
            # Add some history
            for i in range(5):
                date = datetime.utcnow() - timedelta(days=i*7)
                hist_score = max(0, min(100, data["score"] - range(5, 15)[i])) # slightly lower in past
                history = StudentSkillProgress(
                    student_skill_id=skill.id, # We need flush to get ID, but let's commit after loop
                    proficiency_score=hist_score,
                    risk_score=round(1.0 - (hist_score / 100.0), 2),
                    date=date
                )
                # We can't add history yet if skill.id is None. 
                # Let's simple-save skill first.
        
        db.session.commit()
        
        # Now refetch to ensure IDs and add history
        for data in skills_data:
            skill = StudentSkill.query.filter_by(student_id=student.id, skill_name=data["name"]).first()
            if skill:
                 # Check if history exists
                if not skill.progress_history:
                    for i in range(5):
                        date = datetime.utcnow() - timedelta(days=(5-i)*7)
                        hist_score = max(0, min(100, data["score"] - (5-i)*2)) 
                        
                        history = StudentSkillProgress(
                            student_skill_id=skill.id,
                            proficiency_score=hist_score,
                            risk_score=round(1.0 - (hist_score / 100.0), 2),
                            date=date
                        )
                        db.session.add(history)
        
        db.session.commit()
        print("Skills seeded successfully!")

if __name__ == "__main__":
    seed_skills()
