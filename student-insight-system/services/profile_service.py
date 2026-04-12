"""
Profile service — student profile CRUD, CV generation.

Extracted from routes.py: student_profile(), delete_profile(), create_profile().
"""

import os
import logging
from werkzeug.utils import secure_filename

from core.errors import NotFoundError
from core.extensions import db
from models import StudentProfile, User

logger = logging.getLogger(__name__)


class ProfileService:
    """Student profile management — HTTP-unaware."""

    @staticmethod
    def _get_student(user_id):
        student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
        if not student:
            raise NotFoundError("Student not found")
        return student

    @staticmethod
    def get_profile(user_id: str):
        """Return the student profile object."""
        return ProfileService._get_student(user_id)

    @staticmethod
    def update_profile(user_id: str, data, profile_picture_file=None,
                       cover_picture_file=None, upload_root=None) -> None:
        """Update profile fields and optionally upload a picture."""
        student = ProfileService._get_student(user_id)

        student.full_name = data.full_name
        if getattr(data, 'email', None):
            student.user.email = data.email
        if data.university is not None:
            student.university = data.university
        if data.department is not None:
            student.department = data.department
        if data.current_year is not None:
            student.current_year = data.current_year
        if data.cgpa is not None:
            student.current_cgpa = data.cgpa
        if data.career_goal is not None:
            student.career_goal = data.career_goal
        if data.linkedin_profile is not None:
            student.linkedin_profile = data.linkedin_profile
        if data.github_profile is not None:
            student.github_profile = data.github_profile
        if data.bio is not None:
            student.bio = data.bio

        # Handle profile picture
        if upload_root:
            upload_folder = os.path.join(upload_root, 'static', 'uploads', 'profile_pics')
            os.makedirs(upload_folder, exist_ok=True)
            
            if profile_picture_file and profile_picture_file.filename:
                filename = secure_filename(profile_picture_file.filename)
                profile_picture_file.save(os.path.join(upload_folder, filename))
                student.profile_picture = filename
                
            if cover_picture_file and cover_picture_file.filename:
                cover_filename = secure_filename(cover_picture_file.filename)
                cover_picture_file.save(os.path.join(upload_folder, cover_filename))
                student.cover_picture = cover_filename

        db.session.commit()
        logger.info("Profile updated for student_id=%d", student.id)

    @staticmethod
    def delete_profile(user_id: str) -> None:
        """Delete the user and cascade-delete the profile."""
        user = User.query.get(int(user_id))
        if not user:
            raise NotFoundError("User not found")

        student = StudentProfile.query.filter_by(user_id=user.id).first()
        if student:
            s_id = student.id
            from models.teacher import TeacherAssignment, AssignmentTransferRequest
            from models.alerts import Attendance, StudentNote, StudentAlert
            from models.skills import ActionPlan
            from models.assessments import AssignmentSubmission, AssessmentResult
            from models.analytics import StudentInsight
            
            TeacherAssignment.query.filter_by(student_id=s_id).delete()
            AssignmentTransferRequest.query.filter_by(student_id=s_id).delete()
            Attendance.query.filter_by(student_id=s_id).delete()
            StudentNote.query.filter_by(student_id=s_id).delete()
            StudentAlert.query.filter_by(student_id=s_id).delete()
            ActionPlan.query.filter_by(student_id=s_id).delete()
            AssignmentSubmission.query.filter_by(student_id=s_id).delete()
            AssessmentResult.query.filter_by(student_id=s_id).delete()
            StudentInsight.query.filter_by(student_id=s_id).delete()

        db.session.delete(user)
        db.session.commit()
        logger.info("User %d and profile deleted", user.id)

    @staticmethod
    def get_settings_data(user_id: str) -> dict:
        """Build data for the settings page."""
        user = User.query.get(int(user_id))
        student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
        if not student or not user:
            raise NotFoundError("User not found")
        return {"user": user, "profile": student}

    @staticmethod
    def build_cv_data(form) -> dict:
        """Parse CV creation form into a data dict for the template."""
        return {
            "full_name": form.get("full_name"),
            "job_title": form.get("job_title"),
            "email": form.get("email"),
            "phone": form.get("phone"),
            "dob": form.get("dob"),
            "gender": form.get("gender"),
            "address": form.get("address"),
            "website": form.get("website"),
            "summary": form.get("summary"),
            "education": [
                {
                    "date": form.get("edu_date_1"),
                    "school": form.get("edu_school_1"),
                    "details": form.get("edu_detail_1"),
                },
                {
                    "date": form.get("edu_date_2"),
                    "school": form.get("edu_school_2"),
                    "details": form.get("edu_detail_2"),
                },
            ],
            "experience": [
                {
                    "date": form.get("work_date_1"),
                    "company": form.get("work_company_1"),
                    "title": form.get("work_title_1"),
                    "desc": form.get("work_desc_1"),
                },
                {
                    "date": form.get("work_date_2"),
                    "company": form.get("work_company_2"),
                    "title": form.get("work_title_2"),
                    "desc": form.get("work_desc_2"),
                },
            ],
        }
