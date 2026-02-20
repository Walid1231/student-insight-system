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
    and recalculates system fields (hours, consistency, burnout, goal prob).
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
    # Factors: high hours + low productivity + high difficulty = high burnout
    hours = update.total_hours_studied or 0
    productivity = update.productivity_rating or 3  # default medium
    difficulty = update.difficulty_rating or 'Medium'
    mood = update.mood_score or 3

    # Hours component (0-0.4): >30hrs/week is high risk
    hours_factor = min(hours / 30, 1.0) * 0.4

    # Productivity inverse (0-0.25): low productivity = higher burnout
    prod_factor = (1 - (productivity - 1) / 4) * 0.25

    # Difficulty component (0-0.15)
    diff_map = {'Easy': 0, 'Medium': 0.07, 'Hard': 0.15}
    diff_factor = diff_map.get(difficulty, 0.07)

    # Mood inverse (0-0.2): low mood = higher burnout
    mood_factor = (1 - (mood - 1) / 4) * 0.2

    burnout = min(hours_factor + prod_factor + diff_factor + mood_factor, 1.0)
    update.burnout_risk_score = round(burnout, 2)

    # ── 4. Goal achievability probability ──
    # Based on: CGPA trend direction, consistency, effort level
    cgpa = student.current_cgpa or 0
    target = student.target_cgpa or 3.5
    
    # Base probability from how close CGPA is to target
    if target > 0:
        cgpa_ratio = min(cgpa / target, 1.0)
    else:
        cgpa_ratio = 0.5
    
    base_prob = cgpa_ratio * 0.5  # 0-0.5

    # Consistency bonus (0-0.25)
    consistency_bonus = (update.consistency_score or 0) * 0.25

    # Effort bonus (0-0.15): studying regularly
    effort_bonus = min(hours / 20, 1.0) * 0.15

    # Burnout penalty (0-0.1)
    burnout_penalty = burnout * 0.1

    goal_prob = min(base_prob + consistency_bonus + effort_bonus - burnout_penalty, 1.0)
    goal_prob = max(goal_prob, 0.05)  # minimum 5%
    update.goal_achievability_prob = round(goal_prob, 2)

    # ── 5. Status label ──
    if goal_prob >= 0.7:
        update.status_label = 'On Track'
    elif goal_prob >= 0.4:
        update.status_label = 'Needs Attention'
    else:
        update.status_label = 'At Risk'

    db.session.commit()
    return update
