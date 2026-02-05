from app import app, db
from models import StudentProfile, AcademicMetric, StudentSkill, StudentCourse, CareerInterest, AnalyticsResult

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database initialized and tables created successfully!")

if __name__ == "__main__":
    init_db()
