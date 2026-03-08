"""Student profile data access."""

from repositories.base import BaseRepository
from models.student import StudentProfile


class StudentRepository(BaseRepository):
    model = StudentProfile

    @classmethod
    def get_by_user_id(cls, user_id):
        """Look up student by their auth user_id."""
        return cls.model.query.filter_by(user_id=int(user_id)).first()

    @classmethod
    def get_with_skills(cls, student_id):
        """Eagerly load skills for radar chart."""
        from models.skills import StudentSkill
        student = cls.get_by_id(student_id)
        if student:
            # Force load the relationship
            _ = student.skills
        return student
