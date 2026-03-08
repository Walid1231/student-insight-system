"""Academic records and course catalog."""

from core.extensions import db


class CourseCatalog(db.Model):
    """
    The official list of courses.
    Crucial for the 'Strength/Weakness Map' (Core vs GED).
    """
    __tablename__ = 'course_catalog'

    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(150), nullable=False)
    department = db.Column(db.String(100))
    course_type = db.Column(db.String(50))  # 'Core', 'GED', 'Elective'
    credit_value = db.Column(db.Integer, default=3)

    student_records = db.relationship('StudentAcademicRecord', backref='catalog_course', lazy=True)


class StudentAcademicRecord(db.Model):
    """
    Replacement for 'StudentCourse'.
    Links to 'CourseCatalog' to know if it's Core/GED automatically.
    """
    __tablename__ = 'student_academic_records'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course_catalog.id'), nullable=False)

    grade = db.Column(db.String(5))
    grade_point = db.Column(db.Float)
    confidence_score = db.Column(db.Integer)
    semester_taken = db.Column(db.Integer)


class StudentCourse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    course_type = db.Column(db.String(20))
    grade = db.Column(db.String(5))
