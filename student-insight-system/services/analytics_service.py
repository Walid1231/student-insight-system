"""
Analytics service — AI-powered insight report generation.

Extracted from routes.py: student_insight_report().
Wraps the Gemini API calls behind the AIServiceInterface.
"""

import logging
from datetime import datetime

from core.errors import NotFoundError
from core.extensions import db
from models import StudentProfile, StudentInsight

logger = logging.getLogger(__name__)


class AnalyticsService:
    """AI-powered analytics — HTTP-unaware, AI-provider-agnostic."""

    @staticmethod
    def generate_insight_report(user_id: str, form_data: dict, ai_service) -> str:
        """
        Generate an AI insight report from form data.

        Args:
            user_id: JWT identity
            form_data: Dict with department, cgpa, semester_gpas, skills, etc.
            ai_service: AIServiceInterface implementation

        Returns:
            HTML string of the generated report
        """
        department = form_data.get("department", "Computer Science")
        cgpa = form_data.get("cgpa", "3.0")
        semester_gpas = form_data.get("semester_gpas", "2.8, 3.0, 3.2")
        skills = form_data.get("skills", "Python, HTML")
        strong_courses = form_data.get("strong_courses", "Programming")
        weak_courses = form_data.get("weak_courses", "Math")
        interests = form_data.get("interests", "Web Development")

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
           <p>A 2-sentence summary of their current standing.</p>

        2. <h3>🛠 Skills vs. Industry Standards (Gap Analysis)</h3>
           <p>Compare their reported skills against modern industry requirements.</p>

        3. <h3>📉 Remedial Action Plan</h3>
           <ul><li>Identify struggles and suggest 2 specific resources.</li></ul>

        4. <h3>🚀 Career Trajectory & Niche</h3>
           <p>Suggest 2 specific job titles based on interests and strengths.</p>
        """

        report_html = ai_service.generate_text(prompt)

        # Save to database
        try:
            student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
            if student:
                insight = StudentInsight(
                    student_id=student.id,
                    content=report_html,
                    generated_at=datetime.utcnow(),
                )
                db.session.add(insight)
                db.session.commit()
                logger.info("Insight report saved for student_id=%d", student.id)
        except Exception:
            logger.exception("Failed to save insight report to DB")

        return report_html
