"""Career paths, required skills, interests, and student goals."""

from core.extensions import db


class CareerPath(db.Model):
    """
    Standard definitions of careers.
    Used for the 'Career Compatibility' logic.
    """
    __tablename__ = 'career_paths'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    field_category = db.Column(db.String(100))
    description = db.Column(db.Text)

    required_skills = db.relationship('CareerRequiredSkill', backref='career', lazy=True)


class CareerRequiredSkill(db.Model):
    """
    The link between a Career and a Skill.
    Example: 'Software Engineer' requires 'Python' with 'High' importance.
    """
    __tablename__ = 'career_required_skills'

    id = db.Column(db.Integer, primary_key=True)
    career_id = db.Column(db.Integer, db.ForeignKey('career_paths.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    importance_level = db.Column(db.String(20))


class CareerInterest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    field_name = db.Column(db.String(100), nullable=False)
    interest_score = db.Column(db.Float)


class StudentGoal(db.Model):
    """
    Replacement for 'CareerInterest'.
    Links specific CareerPaths to the student with context.
    """
    __tablename__ = 'student_goals'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    career_id = db.Column(db.Integer, db.ForeignKey('career_paths.id'), nullable=False)

    goal_type = db.Column(db.String(50))
    reason = db.Column(db.String(50))
    is_primary = db.Column(db.Boolean, default=False)
