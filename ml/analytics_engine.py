import numpy as np
import json
from sklearn.linear_model import LinearRegression
from models import db, StudentProfile, AcademicMetric, StudentSkill, StudentCourse, CareerInterest, AnalyticsResult

class AnalyticsEngine:
    def __init__(self):
        self.career_keywords = {
            'Software Development': ['Python', 'Java', 'C++', 'JavaScript', 'React', 'Node.js', 'Software Engineering', 'Data Structures', 'Algorithms'],
            'Data Science': ['Python', 'SQL', 'Data Analysis', 'Machine Learning', 'Statistics', 'Calculus', 'Linear Algebra'],
            'AI/ML': ['Python', 'Machine Learning', 'Artificial Intelligence', 'Calculus', 'Linear Algebra', 'Data Analysis'],
            'Cloud Computing': ['AWS', 'Docker', 'Kubernetes', 'Computer Networks', 'Operating Systems', 'Linux'],
            'Cybersecurity': ['Cybersecurity', 'Networks', 'Cryptography', 'Linux', 'Operating Systems'],
            'Web Development': ['JavaScript', 'React', 'Node.js', 'HTML', 'CSS', 'Web Development'],
            'DevOps': ['Docker', 'Kubernetes', 'AWS', 'Linux', 'Scripting', 'CI/CD']
        }

    def predict_next_gpa(self, student_id):
        """Predict next semester GPA using Linear Regression on past grades"""
        metric = AcademicMetric.query.filter_by(student_id=student_id).first()
        if not metric or not metric.semester_gpas:
            return 0.0
            
        gpas = metric.get_gpas()
        if len(gpas) < 2:
            return gpas[0] if gpas else 0.0
            
        X = np.array(range(len(gpas))).reshape(-1, 1)
        y = np.array(gpas)
        
        model = LinearRegression()
        model.fit(X, y)
        
        next_semester_index = np.array([[len(gpas)]])
        prediction = model.predict(next_semester_index)[0]
        return round(min(max(prediction, 0.0), 4.0), 2)

    def analyze_career_interests(self, student_id):
        """AI-driven scoring of career interests based on skills and course performance"""
        skills = StudentSkill.query.filter_by(student_id=student_id).all()
        courses = StudentCourse.query.filter_by(student_id=student_id).all()
        
        student_skills = [s.skill_name for s in skills]
        strong_courses = [c.course_name for c in courses if c.course_type == 'strong']
        
        # Calculate scores for each field
        interest_scores = {}
        for field, keywords in self.career_keywords.items():
            score = 0
            
            # Match skills (weighted higher)
            for skill in student_skills:
                if skill in keywords:
                    score += 15 # High impact
                    
            # Match strong courses
            for course in strong_courses:
                for keyword in keywords:
                    if keyword in course: # Simple substring match
                        score += 10
                        
            # Normalize to 0-100 scale (capped)
            normalized_score = min(score, 100)
            # Add some randomness to simulate "AI uncertainty" / variation
            normalized_score = min(100, normalized_score + np.random.randint(-5, 15))
            
            interest_scores[field] = max(0, normalized_score)
            
        return interest_scores

    def generate_insight_report(self, student_id):
        """Generate full analytics and save to database"""
        predicted_gpa = self.predict_next_gpa(student_id)
        career_scores = self.analyze_career_interests(student_id)
        
        # Save predictions
        analytics = AnalyticsResult.query.filter_by(student_id=student_id).first()
        if not analytics:
            analytics = AnalyticsResult(student_id=student_id)
            
        analytics.predicted_next_gpa = predicted_gpa
        analytics.career_predictions = json.dumps(career_scores)
        
        # Generate skill recommendations based on top career interest
        top_career = max(career_scores, key=career_scores.get)
        needed_skills = self.career_keywords.get(top_career, [])
        student_skills = [s.skill_name for s in StudentSkill.query.filter_by(student_id=student_id).all()]
        
        recommendations = [skill for skill in needed_skills if skill not in student_skills][:5]
        analytics.skill_recommendations = json.dumps(recommendations)
        
        db.session.add(analytics)
        db.session.commit()
        
        return {
            'predicted_gpa': predicted_gpa,
            'career_scores': career_scores,
            'recommendations': recommendations
        }
