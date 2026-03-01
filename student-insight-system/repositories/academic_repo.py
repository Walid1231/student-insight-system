"""Academic record data access."""

from collections import defaultdict
from repositories.base import BaseRepository
from models.academic import StudentAcademicRecord, CourseCatalog
from core.extensions import db


class AcademicRepository(BaseRepository):
    model = StudentAcademicRecord

    @classmethod
    def get_graded_records(cls, student_id):
        """Return (record, catalog_course) pairs where grade_point is not None."""
        return (
            db.session.query(StudentAcademicRecord, CourseCatalog)
            .join(CourseCatalog)
            .filter(
                StudentAcademicRecord.student_id == student_id,
                StudentAcademicRecord.grade_point.isnot(None),
            )
            .all()
        )

    @classmethod
    def records_by_semester(cls, student_id):
        """Return {semester: [(grade_point, credit_value), ...]}."""
        records = cls.get_graded_records(student_id)
        semesters = defaultdict(list)
        for r, c in records:
            cr = c.credit_value or 3
            semesters[r.semester_taken].append((float(r.grade_point), float(cr)))
        return dict(semesters)

    @classmethod
    def course_type_counts(cls, student_id):
        """Return {'Core': n, 'GED': n, 'Elective': n}."""
        all_records = (
            db.session.query(StudentAcademicRecord, CourseCatalog)
            .join(CourseCatalog)
            .filter(StudentAcademicRecord.student_id == student_id)
            .all()
        )
        counts = {"Core": 0, "GED": 0, "Elective": 0}
        for r, c in all_records:
            ct = (c.course_type or "").strip()
            if ct in counts:
                counts[ct] += 1
        return counts
