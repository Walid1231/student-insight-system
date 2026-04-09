"""
models — Domain model package.

Re-exports every model class so existing code continues to work:
    from models import db, User, StudentProfile  # ← unchanged
"""

# Extension instance (re-exported for backward compatibility)
from core.extensions import db  # noqa: F401

# ── Identity ──
from models.user import User, UserToken, PasswordResetToken  # noqa: F401

# ── Student ──
from models.student import StudentProfile, AcademicMetric, StudentSettings  # noqa: F401

# ── Teacher ──
from models.teacher import TeacherProfile, TeacherAssignment, AssignmentTransferRequest  # noqa: F401

# ── Academic Records ──
from models.academic import (  # noqa: F401
    CourseCatalog,
    StudentAcademicRecord,
    StudentCourse,
)

# ── Skills ──
from models.skills import (  # noqa: F401
    Skill,
    StudentSkill,
    StudentSkillProgress,
    ActionPlan,
)

# ── Sessions & Check-ins ──
from models.sessions import StudySession, WeeklyUpdate  # noqa: F401

# ── Career ──
from models.career import (  # noqa: F401
    CareerPath,
    CareerRequiredSkill,
    CareerInterest,
    StudentGoal,
)

# ── Alerts & Notes ──
from models.alerts import Attendance, StudentNote, StudentAlert  # noqa: F401

# ── Assessments ──
from models.assessments import (  # noqa: F401
    Assignment,
    AssignmentSubmission,
    Assessment,
    AssessmentResult,
)

# ── Analytics & AI ──
from models.analytics import (  # noqa: F401
    AnalyticsResult,
    StudentInsight,
    ChatHistory,
)
