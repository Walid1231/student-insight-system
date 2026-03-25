"""
Recalculation engine: rebuilds the current week's WeeklyUpdate from live data.
Called after every save (study session, check-in, grade input, goal change).

Improvements integrated:
  1. Skill Match & Proficiency – primary-goal skill overlap weighted by proficiency
  2. Subject-Specific Grade Weighting – Core courses count more than electives
  3. Rolling 4-week Averages – effort & consistency smoothed over 28 days
"""
from datetime import datetime, timedelta
from models import (
    db, StudentProfile, StudySession, WeeklyUpdate,
    AcademicMetric, StudentGoal, CareerPath, StudentSkill,
    CareerRequiredSkill, StudentAcademicRecord, CourseCatalog, Skill
)


def recalculate_weekly_update(student_id):
    """
    Recompute the current week's WeeklyUpdate row from live data.
    Preserves user-submitted fields (productivity_rating, difficulty_rating, mood_score)
    and recalculates system fields (hours, consistency, burnout, goal prob, status).
    """
    student = StudentProfile.query.get(student_id)
    if not student:
        return

    today = datetime.utcnow().date()
    week_start = today - timedelta(days=today.weekday())  # Monday

    # Find or create this week's update
    update = WeeklyUpdate.query.filter_by(
        student_id=student_id,
        week_start_date=week_start
    ).first()

    if not update:
        update = WeeklyUpdate(
            student_id=student_id,
            week_start_date=week_start
        )
        db.session.add(update)

    # ── 1. Total hours studied this week ──
    week_sessions = StudySession.query.filter(
        StudySession.student_id == student_id,
        StudySession.date >= week_start,
        StudySession.date <= week_start + timedelta(days=6)
    ).all()

    total_minutes = sum(s.duration_minutes for s in week_sessions)
    update.total_hours_studied = round(total_minutes / 60, 1)

    # ── 2. Consistency score (days active / 7) — kept for the DB column ──
    active_days = len(set(s.date for s in week_sessions))
    update.consistency_score = round(active_days / 7, 2)

    # ── 3. Burnout risk score ──
    hours = update.total_hours_studied or 0
    productivity = update.productivity_rating or 3
    difficulty = update.difficulty_rating or 'Medium'
    mood = update.mood_score or 3

    hours_factor = min(hours / 30, 1.0) * 0.35
    prod_factor = (1 - (productivity - 1) / 4) * 0.25
    diff_map = {'Easy': 0.02, 'Medium': 0.10, 'Hard': 0.20}
    diff_factor = diff_map.get(difficulty, 0.10)
    mood_factor = (1 - (mood - 1) / 4) * 0.2

    burnout = min(hours_factor + prod_factor + diff_factor + mood_factor, 1.0)
    update.burnout_risk_score = round(burnout, 2)

    # ══════════════════════════════════════════════════════════════
    #  4. Goal achievability probability  (IMPROVED)
    #
    #  Now uses 5 signals instead of 4:
    #    A. Weighted CGPA        (20%)  – Core courses count 1.5×
    #    B. Rolling effort       (20%)  – 4-week average study hours
    #    C. Self-reported perf   (25%)  – productivity + mood
    #    D. Rolling consistency  (15%)  – 4-week average days active
    #    E. Skill proficiency    (20%)  – proficiency match vs primary goal
    #  Burnout still acts as a penalty.
    # ══════════════════════════════════════════════════════════════

    # ── Signal A: Weighted CGPA (Subject-Specific Grade Weighting) ──
    target = student.target_cgpa or 3.5
    adjusted_cgpa = _calc_weighted_cgpa(student_id, student.current_cgpa)
    cgpa_signal = min(adjusted_cgpa / target, 1.0) if target > 0 else 0.5

    # ── Signal B: Rolling 4-week effort ──
    four_week_start = today - timedelta(days=28)
    four_week_sessions = StudySession.query.filter(
        StudySession.student_id == student_id,
        StudySession.date >= four_week_start,
        StudySession.date <= today
    ).all()

    four_week_hours = sum(s.duration_minutes for s in four_week_sessions) / 60
    avg_weekly_hours = four_week_hours / 4
    effort_signal = min(avg_weekly_hours / 25, 1.0) if avg_weekly_hours > 0 else 0

    # ── Signal C: Self-reported performance ──
    perf_signal = ((productivity - 1) / 4 + (mood - 1) / 4) / 2

    # ── Signal D: Rolling 4-week consistency ──
    active_days_28 = len(set(s.date for s in four_week_sessions))
    consistency_signal = round(active_days_28 / 28, 2)

    # ── Signal E: Skill proficiency match against primary goal ──
    skill_signal = _calc_skill_signal(student_id)

    # Weighted combination (5 signals)
    raw_prob = (
        cgpa_signal       * 0.20 +
        effort_signal     * 0.20 +
        perf_signal       * 0.25 +
        consistency_signal * 0.15 +
        skill_signal      * 0.20
    )

    # Burnout penalty
    burnout_penalty = burnout * 0.15
    goal_prob = max(raw_prob - burnout_penalty, 0.05)
    goal_prob = min(goal_prob, 1.0)

    update.goal_achievability_prob = round(goal_prob, 2)

    # ── 5. Status label ──
    weekly_perf = (
        (productivity - 1) / 4 * 0.35 +
        (mood - 1) / 4 * 0.20 +
        (1 - diff_map.get(difficulty, 0.10)) * 0.15 +
        consistency_signal * 0.15 +
        min(hours / 20, 1.0) * 0.15
    )

    health_score = goal_prob * 0.40 + weekly_perf * 0.60

    if health_score >= 0.55:
        update.status_label = 'On Track'
    elif health_score >= 0.35:
        update.status_label = 'Needs Attention'
    else:
        update.status_label = 'At Risk'

    db.session.commit()
    return update


# ─────────────────────────────────────────────────────────────
#  Helper: Weighted CGPA (Subject-Specific Grade Weighting)
# ─────────────────────────────────────────────────────────────
def _calc_weighted_cgpa(student_id, fallback_cgpa):
    """
    Compute a weighted CGPA where Core courses count 1.5×,
    Electives count 0.8×, and GED counts 1.0×.
    Falls back to the raw current_cgpa if no academic records exist.
    """
    records = (
        db.session.query(StudentAcademicRecord, CourseCatalog)
        .join(CourseCatalog, StudentAcademicRecord.course_id == CourseCatalog.id)
        .filter(StudentAcademicRecord.student_id == student_id)
        .all()
    )

    if not records:
        return fallback_cgpa or 0

    multiplier_map = {'Core': 1.5, 'Elective': 0.8, 'GED': 1.0}
    weighted_points = 0
    weighted_credits = 0

    for rec, course in records:
        if rec.grade_point is None:
            continue
        credits = course.credit_value or 3
        mult = multiplier_map.get(course.course_type, 1.0)
        weighted_points += rec.grade_point * credits * mult
        weighted_credits += credits * mult

    if weighted_credits == 0:
        return fallback_cgpa or 0

    return round(weighted_points / weighted_credits, 2)


# ─────────────────────────────────────────────────────────────
#  Helper: Skill proficiency match against primary career goal
# ─────────────────────────────────────────────────────────────
def _calc_skill_signal(student_id):
    """
    Find the student's primary goal career and compute a proficiency-
    weighted skill match score (0.0 – 1.0).
    If no primary goal or no required skills, returns a neutral 0.5.
    """
    primary_goal = StudentGoal.query.filter_by(
        student_id=student_id,
        is_primary=True
    ).first()

    if not primary_goal or not primary_goal.career_id:
        return 0.5  # neutral when no goal is set

    # Get required skill names for this career
    required = (
        db.session.query(Skill.skill_name)
        .join(CareerRequiredSkill, CareerRequiredSkill.skill_id == Skill.id)
        .filter(CareerRequiredSkill.career_id == primary_goal.career_id)
        .all()
    )
    required_names = {r.skill_name.lower().strip() for r in required}

    if not required_names:
        return 0.5  # career has no defined required skills

    total_required = len(required_names)
    max_proficiency = total_required * 100  # each skill's max is 100

    # Get the student's matching skills with their proficiency
    student_skills = StudentSkill.query.filter_by(student_id=student_id).all()
    matched_proficiency = sum(
        (sk.proficiency_score or 0)
        for sk in student_skills
        if sk.skill_name.lower().strip() in required_names
    )

    return min(matched_proficiency / max_proficiency, 1.0) if max_proficiency > 0 else 0.5
