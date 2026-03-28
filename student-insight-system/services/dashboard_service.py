"""
Dashboard data aggregation service.

Extracts the 220+ line student_dashboard() data aggregation logic
into a testable, HTTP-unaware service.
"""

import logging
from datetime import date, timedelta
from collections import defaultdict

from sqlalchemy import func

from core.errors import NotFoundError
from core.extensions import db
from models import (
    StudentProfile, StudentSkill, StudySession, WeeklyUpdate,
    StudentAcademicRecord, CourseCatalog, StudentGoal, CareerPath,
    CareerRequiredSkill, Skill as SkillModel,
)

logger = logging.getLogger(__name__)


class DashboardService:
    """Aggregates all dashboard widget data — HTTP-unaware."""

    @staticmethod
    def get_student_or_404(user_id):
        """Resolve user_id → StudentProfile or raise NotFoundError."""
        try:
            student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
        except (ValueError, TypeError):
            raise NotFoundError("Invalid user identity")
        if not student:
            raise NotFoundError("Student profile not found")
        return student

    @staticmethod
    def get_dashboard_data(user_id: str) -> dict:
        """Build the complete data dict consumed by student_dashboard.html."""
        student = DashboardService.get_student_or_404(user_id)

        # ── 1. CGPA TREND ──
        records_raw = (
            db.session.query(StudentAcademicRecord, CourseCatalog)
            .join(CourseCatalog, StudentAcademicRecord.course_id == CourseCatalog.id)
            .filter(StudentAcademicRecord.student_id == student.id)
            .all()
        )

        semesters = defaultdict(list)
        for r, c in records_raw:
            # Skip records with missing grade points
            if r.grade_point is None:
                continue
            semesters[r.semester_taken].append((r.grade_point, c.credit_value or 3))

        # Compute cumulative weighted CGPA across semesters
        cgpa_labels, cgpa_values = [], []
        cumulative_points, cumulative_credits = 0.0, 0
        for sem in sorted(semesters.keys()):
            grades = semesters[sem]
            sem_credits = sum(cr for _, cr in grades)
            sem_points = sum(gp * cr for gp, cr in grades)
            cumulative_points += sem_points
            cumulative_credits += sem_credits
            if cumulative_credits > 0:
                cgpa_labels.append(f"Sem {sem}")
                cgpa_values.append(round(cumulative_points / cumulative_credits, 2))

        current_cgpa = student.current_cgpa or 0

        # ── 2. STRENGTH & WEAKNESS RADAR ──
        skills = StudentSkill.query.filter_by(student_id=student.id).order_by(
            StudentSkill.proficiency_score.desc()
        ).all()
        radar_labels = [s.skill_name for s in skills[:6]]
        radar_scores = [s.proficiency_score or 50 for s in skills[:6]]

        # ── 3. CORE vs GED ──
        core_count = sum(1 for r, c in records_raw if c.course_type == 'Core')
        ged_count = sum(1 for r, c in records_raw if c.course_type == 'GED')
        elective_count = sum(1 for r, c in records_raw if c.course_type == 'Elective')

        # ── 4. WEEKLY STUDY HOURS ──
        today = date.today()
        window_start = today - timedelta(days=6)

        day_map = {
            window_start + timedelta(days=i): 0.0
            for i in range(7)
        }

        rows = (
            db.session.query(
                StudySession.date,
                func.sum(StudySession.duration_minutes).label("total_minutes"),
            )
            .filter(
                StudySession.student_id == student.id,
                StudySession.date >= window_start,
                StudySession.date <= today,
            )
            .group_by(StudySession.date)
            .order_by(StudySession.date)
            .all()
        )
        for row in rows:
            if row.date in day_map:
                day_map[row.date] = round(row.total_minutes / 60, 1)

        weekly_labels = [d.strftime('%a ') + str(d.day) for d in day_map]
        weekly_hours = list(day_map.values())
        has_recent_sessions = any(h > 0 for h in weekly_hours)

        # ── 5. SKILL EFFORT ──
        rolling14_start = today - timedelta(days=13)
        midpoint = today - timedelta(days=6)
        sessions_14d = StudySession.query.filter(
            StudySession.student_id == student.id,
            StudySession.date >= rolling14_start,
            StudySession.date <= today,
            StudySession.related_skill.isnot(None),
        ).all()

        skill_effort = defaultdict(lambda: [0.0, 0.0])
        for s in sessions_14d:
            hrs = round(s.duration_minutes / 60, 1)
            if s.date < midpoint:
                skill_effort[s.related_skill][0] += hrs
            else:
                skill_effort[s.related_skill][1] += hrs

        top_skills = sorted(skill_effort.items(), key=lambda x: sum(x[1]), reverse=True)[:4]
        effort_labels = [s[0] for s in top_skills]
        effort_week_a = [round(s[1][0], 1) for s in top_skills]
        effort_week_b = [round(s[1][1], 1) for s in top_skills]

        # ── 6. CAREER COMPATIBILITY ──
        goals_list = StudentGoal.query.filter_by(student_id=student.id).order_by(
            StudentGoal.is_primary.desc()
        ).all()
        student_skill_names = {s.skill_name for s in skills}
        careers = []

        for g in goals_list[:3]:
            career = CareerPath.query.get(g.career_id)
            if not career:
                continue
            required = CareerRequiredSkill.query.filter_by(career_id=g.career_id).count()
            matched = 0
            if student_skill_names:
                matched = (
                    db.session.query(CareerRequiredSkill)
                    .join(SkillModel, CareerRequiredSkill.skill_id == SkillModel.id)
                    .filter(
                        CareerRequiredSkill.career_id == g.career_id,
                        SkillModel.skill_name.in_(student_skill_names),
                    )
                    .count()
                )
            # 0% when no required skills are defined for this career
            if required > 0:
                match_pct = min(int(matched / required * 100), 100)
                no_data = False
            else:
                match_pct = 0
                no_data = True
            careers.append({
                "role": career.title,
                "match": match_pct,
                "no_data": no_data,
                "is_primary": g.is_primary
            })

        # Sort so primary is always first, then by match %
        careers = sorted(careers, key=lambda x: (x['is_primary'], x['match']), reverse=True)

        # ── 7. BURNOUT RISK ──
        latest_update = (
            WeeklyUpdate.query
            .filter_by(student_id=student.id)
            .order_by(WeeklyUpdate.created_at.desc())
            .first()
        )
        burnout_score = latest_update.burnout_risk_score if latest_update else 0
        burnout_pct = int(burnout_score * 100) if burnout_score else 0
        if burnout_pct < 40:
            burnout_label, burnout_message = "Low Risk", "Keep it up!"
        elif burnout_pct < 70:
            burnout_label, burnout_message = "Medium Risk", "Watch your pace"
        else:
            burnout_label, burnout_message = "High Risk", "Take a break!"

        # ── 8. GOAL ACHIEVABILITY ──
        goal_prob = int(latest_update.goal_achievability_prob * 100) if (
            latest_update and latest_update.goal_achievability_prob) else 0
        primary_goal = StudentGoal.query.filter_by(
            student_id=student.id, is_primary=True
        ).first()
        target_career = ""
        target_gpa = student.target_cgpa or (
            round(float(current_cgpa) + 0.2, 1) if current_cgpa else 3.5
        )
        if primary_goal:
            cp = CareerPath.query.get(primary_goal.career_id)
            if cp:
                target_career = cp.title

        # ── QUICK STATS ──
        total_credits = sum(c.credit_value for _, c in records_raw)
        total_sessions = StudySession.query.filter_by(student_id=student.id).count()

        logger.info(
            "Dashboard data loaded for student_id=%d", student.id,
        )

        return {
            "name": student.full_name,
            "cgpa": current_cgpa,
            "total_credits": total_credits,
            "goals_count": len(goals_list),
            "sessions_count": total_sessions,
            "cgpa_labels": cgpa_labels,
            "cgpa_values": cgpa_values,
            "radar_labels": radar_labels,
            "radar_scores": radar_scores,
            "core_count": core_count,
            "ged_count": ged_count,
            "elective_count": elective_count,
            "weekly_labels": weekly_labels,
            "weekly_hours": weekly_hours,
            "effort_labels": effort_labels,
            "effort_week_a": effort_week_a,
            "effort_week_b": effort_week_b,
            "careers": careers,
            "burnout_pct": burnout_pct,
            "burnout_label": burnout_label,
            "burnout_message": burnout_message,
            "goal_prob": goal_prob,
            "target_gpa": target_gpa,
            "target_career": target_career,
            "has_grades": len(records_raw) > 0,
            "has_skills": len(skills) > 0,
            "has_goals": len(goals_list) > 0,
            "has_sessions": total_sessions > 0,
            "has_recent_sessions": has_recent_sessions,
            "has_checkin": latest_update is not None,
            # Internal — for onboarding redirect check
            "_is_new_student": (
                not records_raw and not skills
                and not goals_list and total_sessions == 0
            ),
        }

    @staticmethod
    def get_onboarding_data(user_id: str) -> dict:
        """Build onboarding checklist data."""
        student = DashboardService.get_student_or_404(user_id)

        has_grades = StudentAcademicRecord.query.filter_by(
            student_id=student.id
        ).count() > 0
        has_skills = StudentSkill.query.filter_by(
            student_id=student.id
        ).count() > 0
        has_sessions = StudySession.query.filter_by(
            student_id=student.id
        ).count() > 0
        has_goals = StudentGoal.query.filter_by(
            student_id=student.id
        ).count() > 0

        steps_done = sum([has_grades, has_skills, has_sessions, has_goals])

        return {
            "name": student.full_name,
            "has_grades": has_grades,
            "has_skills": has_skills,
            "has_sessions": has_sessions,
            "has_goals": has_goals,
            "steps_done": steps_done,
            "all_complete": steps_done == 4,
        }
