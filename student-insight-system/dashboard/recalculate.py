"""
Recalculation engine: rebuilds the current week's WeeklyUpdate from live data.
Called after every save (study session, check-in, grade input, goal change).
"""
from datetime import datetime, timedelta
from models import (
    db, StudentProfile, StudySession, WeeklyUpdate,
    AcademicMetric, StudentGoal, CareerPath, StudentSkill,
    CareerRequiredSkill
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
    sessions = StudySession.query.filter(
        StudySession.student_id == student_id,
        StudySession.date >= week_start,
        StudySession.date <= week_start + timedelta(days=6)
    ).all()

    total_minutes = sum(s.duration_minutes for s in sessions)
    update.total_hours_studied = round(total_minutes / 60, 1)

    # ── 2. Consistency score (days active / 7) ──
    active_days = len(set(s.date for s in sessions))
    update.consistency_score = round(active_days / 7, 2)

    # ── 3. Burnout risk score ──
    # Combines: hours overload + low self-reported performance + difficulty
    hours = update.total_hours_studied or 0
    productivity = update.productivity_rating or 3
    difficulty = update.difficulty_rating or 'Medium'
    mood = update.mood_score or 3

    # Hours overload (0-0.35): >30hrs/week is high risk
    hours_factor = min(hours / 30, 1.0) * 0.35

    # Productivity inverse (0-0.25): low productivity = higher burnout
    prod_factor = (1 - (productivity - 1) / 4) * 0.25

    # Difficulty (0-0.2)
    diff_map = {'Easy': 0.02, 'Medium': 0.10, 'Hard': 0.20}
    diff_factor = diff_map.get(difficulty, 0.10)

    # Mood inverse (0-0.2): low mood = higher burnout
    mood_factor = (1 - (mood - 1) / 4) * 0.2

    burnout = min(hours_factor + prod_factor + diff_factor + mood_factor, 1.0)
    update.burnout_risk_score = round(burnout, 2)

    # ── 4. Goal achievability probability ──
    # Balanced formula using 4 signals:
    #   - CGPA progress (how close to target)
    #   - Weekly effort (study hours)
    #   - Self-reported performance (productivity + mood)
    #   - Consistency (days active)
    # Burnout acts as a penalty.

    cgpa = student.current_cgpa or 0
    target = student.target_cgpa or 3.5

    # Signal A: CGPA proximity (0.0 – 1.0)
    if target > 0:
        cgpa_signal = min(cgpa / target, 1.0)
    else:
        cgpa_signal = 0.5

    # Signal B: Weekly effort (0.0 – 1.0), 15h/week = solid, caps at 25h
    effort_signal = min(hours / 25, 1.0) if hours > 0 else 0

    # Signal C: Self-reported performance (0.0 – 1.0)
    # Average of productivity (1-5) and mood (1-5), normalized
    perf_signal = ((productivity - 1) / 4 + (mood - 1) / 4) / 2

    # Signal D: Consistency (0.0 – 1.0), already computed
    consistency_signal = update.consistency_score or 0

    # Weighted combination
    # CGPA 25%, Effort 25%, Performance 30%, Consistency 20%
    raw_prob = (
        cgpa_signal * 0.25 +
        effort_signal * 0.25 +
        perf_signal * 0.30 +
        consistency_signal * 0.20
    )

    # Burnout penalty: high burnout caps achievability
    burnout_penalty = burnout * 0.15
    goal_prob = max(raw_prob - burnout_penalty, 0.05)
    goal_prob = min(goal_prob, 1.0)

    update.goal_achievability_prob = round(goal_prob, 2)

    # ── 5. Status label ──
    # Uses a composite "weekly health" score that blends goal prob
    # with direct weekly performance signals, so a great week
    # can still produce "On Track" even if CGPA has room to grow.

    # Weekly performance score (0-1): how well the student did THIS week
    weekly_perf = (
        (productivity - 1) / 4 * 0.35 +      # productivity weight
        (mood - 1) / 4 * 0.20 +               # mood weight
        (1 - diff_map.get(difficulty, 0.10)) * 0.15 +  # easier = better score
        consistency_signal * 0.15 +            # consistency weight
        min(hours / 20, 1.0) * 0.15            # effort weight
    )

    # Blend: 40% goal probability + 60% weekly performance
    health_score = goal_prob * 0.40 + weekly_perf * 0.60

    if health_score >= 0.55:
        update.status_label = 'On Track'
    elif health_score >= 0.35:
        update.status_label = 'Needs Attention'
    else:
        update.status_label = 'At Risk'

    db.session.commit()
    return update
