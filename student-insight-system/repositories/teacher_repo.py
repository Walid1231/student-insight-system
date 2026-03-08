"""Teacher profile and assignment data access."""

from repositories.base import BaseRepository
from models.teacher import TeacherProfile, TeacherAssignment
from models.student import StudentProfile
from core.extensions import db


class TeacherRepository(BaseRepository):
    model = TeacherProfile

    @classmethod
    def get_by_user_id(cls, user_id):
        """Look up teacher by their auth user_id."""
        return cls.model.query.filter_by(user_id=int(user_id)).first()

    @classmethod
    def get_assigned_students(cls, teacher_id):
        """Return StudentProfile list for all students assigned to this teacher."""
        assignments = TeacherAssignment.query.filter_by(teacher_id=teacher_id).all()
        student_ids = [a.student_id for a in assignments]
        if not student_ids:
            return []
        return StudentProfile.query.filter(StudentProfile.id.in_(student_ids)).all()

    @classmethod
    def get_unassigned_students(cls, teacher_id):
        """Return students NOT yet assigned to this teacher."""
        assigned_ids = (
            db.session.query(TeacherAssignment.student_id)
            .filter(TeacherAssignment.teacher_id == teacher_id)
            .subquery()
        )
        return (
            StudentProfile.query
            .filter(~StudentProfile.id.in_(assigned_ids))
            .all()
        )
