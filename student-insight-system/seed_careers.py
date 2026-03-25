import os
import sys

# Ensure models and app can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, CareerPath
from dashboard.routes import DEPT_CAREERS_SKILLS

def seed_missing_careers():
    app = create_app()
    with app.app_context():
        added = 0
        for dept_name, data in DEPT_CAREERS_SKILLS.items():
            for career_title in data.get("careers", []):
                # Check if it exists
                existing = CareerPath.query.filter(
                    db.func.lower(CareerPath.title) == career_title.lower()
                ).first()
                if not existing:
                    cp = CareerPath(
                        title=career_title,
                        field_category=dept_name,
                        description=f"Career path for {career_title} professionals."
                    )
                    db.session.add(cp)
                    added += 1
                    print(f"Added: {career_title}")
        db.session.commit()
        print(f"Total new careers added: {added}")

if __name__ == "__main__":
    seed_missing_careers()
