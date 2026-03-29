"""
Academic service — CGPA, grades, goals management.

Extracted from routes.py: goals_grades(), add_grade(), _recalculate_cgpa(),
save_target_cgpa(), add_goal(), delete_goal(), set_primary_goal(), delete_grade().
"""

import json
import logging
from collections import defaultdict

from core.errors import NotFoundError
from core.extensions import db
from models import (
    StudentProfile, StudentAcademicRecord, CourseCatalog, AcademicMetric,
    StudentSkill, StudentGoal, CareerPath, CareerRequiredSkill, Skill,
)

logger = logging.getLogger(__name__)

# Grade → GPA mapping
GRADE_MAP = {
    'A+': 4.0, 'A': 4.0, 'A-': 3.7,
    'B+': 3.3, 'B': 3.0, 'B-': 2.7,
    'C+': 2.3, 'C': 2.0,
    'D': 1.0, 'F': 0.0,
}


class AcademicService:
    """Academic records, grades, goals — HTTP-unaware."""

    @staticmethod
    def _get_student(user_id):
        student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
        if not student:
            raise NotFoundError("Student profile not found")
        return student

    # ── Goals & Grades Page Data ──────────────────────────────

    @staticmethod
    def get_goals_grades_data(user_id: str) -> dict:
        """Build the complete data dict for goals_grades.html."""
        student = AcademicService._get_student(user_id)

        # Skills filtered by department
        student_dept = (student.department or "").strip()
        if student_dept:
            all_skills = Skill.query.filter(
                db.or_(
                    Skill.department == student_dept,
                    Skill.department == None,  # noqa: E711
                )
            ).order_by(Skill.skill_name).all()
        else:
            all_skills = Skill.query.order_by(Skill.skill_name).all()

        student_skills = StudentSkill.query.filter_by(student_id=student.id).all()
        student_skill_id_set = {ss.skill_id for ss in student_skills if ss.skill_id}

        # Matching careers
        matching_careers = []
        if student_skill_id_set:
            career_links = (
                db.session.query(
                    CareerRequiredSkill.career_id,
                    db.func.count(CareerRequiredSkill.id).label('match_count'),
                )
                .filter(CareerRequiredSkill.skill_id.in_(student_skill_id_set))
                .group_by(CareerRequiredSkill.career_id)
                .order_by(db.desc('match_count'))
                .all()
            )
            for career_id, match_count in career_links:
                career = CareerPath.query.get(career_id)
                if career:
                    existing_goal = StudentGoal.query.filter_by(
                        student_id=student.id, career_id=career_id
                    ).first()
                    
                    req_skills = (
                        db.session.query(Skill)
                        .join(CareerRequiredSkill, Skill.id == CareerRequiredSkill.skill_id)
                        .filter(CareerRequiredSkill.career_id == career.id)
                        .all()
                    )
                    
                    skill_list = []
                    for s in req_skills:
                        skill_list.append({
                            'id': s.id,
                            'name': s.skill_name,
                            'matched': s.id in student_skill_id_set
                        })

                    matching_careers.append({
                        'id': career.id,
                        'title': career.title,
                        'field_category': career.field_category,
                        'match_count': match_count,
                        'total_req': len(skill_list),
                        'skills': skill_list,
                        'goal_id': existing_goal.id if existing_goal else None,
                    })

        # Goals with career titles and match counts
        goals_raw = StudentGoal.query.filter_by(student_id=student.id).all()
        goal_career_ids = {g.career_id: g.id for g in goals_raw}

        goals = []
        for g in goals_raw:
            career = CareerPath.query.get(g.career_id)
            if not career:
                continue

            req_skills = (
                db.session.query(Skill)
                .join(CareerRequiredSkill, Skill.id == CareerRequiredSkill.skill_id)
                .filter(CareerRequiredSkill.career_id == g.career_id)
                .all()
            )
            
            skill_list = []
            matches_count = 0
            for s in req_skills:
                is_matched = s.id in student_skill_id_set
                if is_matched: matches_count += 1
                skill_list.append({
                    'id': s.id,
                    'name': s.skill_name,
                    'matched': is_matched
                })
            
            goals.append({
                'id': g.id,
                'career_id': g.career_id,
                'career_title': career.title,
                'goal_type': g.goal_type,
                'is_primary': g.is_primary,
                'match_count': matches_count,
                'total_req': len(skill_list),
                'skills': skill_list,
                'field_category': career.field_category
            })

        # Academic records
        records_raw = (
            db.session.query(StudentAcademicRecord, CourseCatalog)
            .join(CourseCatalog, StudentAcademicRecord.course_id == CourseCatalog.id)
            .filter(StudentAcademicRecord.student_id == student.id)
            .order_by(StudentAcademicRecord.semester_taken)
            .all()
        )
        records = [{
            'id': r.id,
            'course_name': c.course_name,
            'course_type': c.course_type,
            'semester_taken': r.semester_taken,
            'grade': r.grade,
            'grade_point': r.grade_point,
            'credit_value': c.credit_value,
        } for r, c in records_raw]

        # All careers for manual selection
        all_career_paths = CareerPath.query.order_by(CareerPath.title).all()

        # Full course catalog for the grade dropdown
        all_courses = CourseCatalog.query.order_by(CourseCatalog.course_name).all()

        return {
            "student": student,
            "all_skills": all_skills,
            "student_dept": student_dept,
            "student_skill_ids": student_skill_id_set,
            "student_skills": student_skills,
            "matching_careers": matching_careers,
            "goal_career_ids": goal_career_ids,
            "goals": goals,
            "records": records,
            "all_careers": all_career_paths,
            "all_courses": all_courses,
        }

    # ── Grade Management ──────────────────────────────────────

    @staticmethod
    def add_grade(user_id: str, data) -> None:
        """Add a grade record, find-or-create the course, recalculate CGPA."""
        student = AcademicService._get_student(user_id)

        catalog_course = CourseCatalog.query.filter(
            db.func.lower(CourseCatalog.course_name) == data.course_name.lower()
        ).first()

        if not catalog_course:
            catalog_course = CourseCatalog(
                course_name=data.course_name,
                department=student.department or "General",
                course_type=data.course_type,
                credit_value=data.credit_value,
            )
            db.session.add(catalog_course)
            db.session.flush()
        else:
            if catalog_course.credit_value != data.credit_value:
                catalog_course.credit_value = data.credit_value

        record = StudentAcademicRecord(
            student_id=student.id,
            course_id=catalog_course.id,
            grade=data.grade,
            grade_point=GRADE_MAP.get(data.grade, 0),
            semester_taken=data.semester,
        )
        db.session.add(record)
        db.session.commit()

        AcademicService.recalculate_cgpa(student)

        from dashboard.recalculate import recalculate_weekly_update
        recalculate_weekly_update(student.id)

        logger.info("Grade added for student_id=%d, course=%s",
                     student.id, data.course_name)

    @staticmethod
    def delete_grade(user_id: str, record_id: int) -> None:
        """Delete a grade record and recalculate CGPA."""
        student = AcademicService._get_student(user_id)

        record = StudentAcademicRecord.query.filter_by(
            id=record_id, student_id=student.id
        ).first()
        if record:
            db.session.delete(record)
            db.session.commit()
            AcademicService.recalculate_cgpa(student)
            logger.info("Grade %d deleted for student_id=%d", record_id, student.id)

    # ── CGPA Recalculation ────────────────────────────────────

    @staticmethod
    def recalculate_cgpa(student) -> None:
        """Recalculate semester GPAs and overall CGPA from academic records."""
        records = (
            db.session.query(StudentAcademicRecord, CourseCatalog)
            .join(CourseCatalog, StudentAcademicRecord.course_id == CourseCatalog.id)
            .filter(StudentAcademicRecord.student_id == student.id)
            .all()
        )

        if not records:
            student.current_cgpa = None
            db.session.commit()
            return

        semesters = defaultdict(list)
        for r, c in records:
            semesters[r.semester_taken].append((r.grade_point or 0, c.credit_value or 3))

        semester_gpas = []
        total_points = 0
        total_credits = 0
        for sem_num in sorted(semesters.keys()):
            sem_points = sum(gp * cr for gp, cr in semesters[sem_num])
            sem_credits = sum(cr for _, cr in semesters[sem_num])
            sem_gpa = round(sem_points / sem_credits, 2) if sem_credits > 0 else 0
            semester_gpas.append(sem_gpa)
            total_points += sem_points
            total_credits += sem_credits

        overall_cgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0

        student.current_cgpa = overall_cgpa
        student.completed_credits = total_credits

        metric = AcademicMetric.query.filter_by(student_id=student.id).first()
        if not metric:
            metric = AcademicMetric(student_id=student.id)
            db.session.add(metric)
        metric.semester_gpas = json.dumps(semester_gpas)
        metric.total_credits = total_credits

        db.session.commit()
        logger.info("CGPA recalculated for student_id=%d → %.2f",
                     student.id, overall_cgpa)

    # ── Target CGPA ───────────────────────────────────────────

    @staticmethod
    def save_target_cgpa(user_id: str, target: float) -> None:
        """Update student's target CGPA and recalculate."""
        student = AcademicService._get_student(user_id)
        student.target_cgpa = target
        db.session.commit()

        from dashboard.recalculate import recalculate_weekly_update
        recalculate_weekly_update(student.id)

    # ── Goal Management ───────────────────────────────────────

    @staticmethod
    def add_goal(user_id: str, career_id: int, goal_type: str = "Long Term"):
        """Add a career goal. Returns goal ID if created, None if duplicate."""
        student = AcademicService._get_student(user_id)

        existing = StudentGoal.query.filter_by(
            student_id=student.id, career_id=career_id
        ).first()
        if existing:
            return existing.id

        is_first = not StudentGoal.query.filter_by(student_id=student.id).first()
        goal = StudentGoal(
            student_id=student.id,
            career_id=career_id,
            goal_type=goal_type,
            is_primary=is_first,
        )
        db.session.add(goal)
        db.session.commit()

        from dashboard.recalculate import recalculate_weekly_update
        recalculate_weekly_update(student.id)
        logger.info("Goal added for student_id=%d, career_id=%d", student.id, career_id)
        return goal.id

    @staticmethod
    def delete_goal(user_id: str, goal_id: int) -> None:
        """Delete a career goal."""
        student = AcademicService._get_student(user_id)
        goal = StudentGoal.query.filter_by(id=goal_id, student_id=student.id).first()
        if goal:
            db.session.delete(goal)
            db.session.commit()

    @staticmethod
    def set_primary_goal(user_id: str, goal_id: int) -> None:
        """Set a goal as primary, unset all others."""
        student = AcademicService._get_student(user_id)

        StudentGoal.query.filter_by(student_id=student.id).update({"is_primary": False})
        goal = StudentGoal.query.filter_by(id=goal_id, student_id=student.id).first()
        if goal:
            goal.is_primary = True
        db.session.commit()

        from dashboard.recalculate import recalculate_weekly_update
        recalculate_weekly_update(student.id)

    # ── Skills Management ──────────────────────────────────────

    @staticmethod
    def add_skill(user_id: str, skill_name: str) -> None:
        """Add a free-text skill. Auto-creates master Skill row if new."""
        from datetime import datetime
        student = AcademicService._get_student(user_id)
        name = skill_name.strip()
        if not name:
            return

        # Prevent duplicates for this student
        existing = StudentSkill.query.filter_by(
            student_id=student.id, skill_name=name
        ).first()
        if existing:
            return

        # Auto-create in master Skill table if it doesn't exist
        master = Skill.query.filter(
            db.func.lower(Skill.skill_name) == name.lower()
        ).first()
        if not master:
            master = Skill(skill_name=name, department=None)
            db.session.add(master)
            db.session.flush()

        new_ss = StudentSkill(
            student_id=student.id,
            skill_id=master.id,
            skill_name=master.skill_name,  # use canonical casing
            proficiency_score=50,
            last_updated=datetime.utcnow(),
        )
        db.session.add(new_ss)
        db.session.commit()
        logger.info("Skill '%s' added for student_id=%d", name, student.id)

    @staticmethod
    def remove_skill(user_id: str, student_skill_id: int) -> None:
        """Remove a specific StudentSkill by its ID."""
        student = AcademicService._get_student(user_id)
        ss = StudentSkill.query.filter_by(
            id=student_skill_id, student_id=student.id
        ).first()
        if ss:
            db.session.delete(ss)
            db.session.commit()
            logger.info("Skill id=%d removed for student_id=%d",
                         student_skill_id, student.id)

    @staticmethod
    def save_skills(user_id: str, selected_skill_ids: list[int]) -> None:
        """Legacy: Sync student skills based on selected skill IDs."""
        from datetime import datetime
        student = AcademicService._get_student(user_id)

        selected_skills = (
            Skill.query.filter(Skill.id.in_(selected_skill_ids)).all()
            if selected_skill_ids else []
        )
        selected_names = {s.skill_name for s in selected_skills}

        current_skills = StudentSkill.query.filter_by(student_id=student.id).all()
        current_names = {ss.skill_name for ss in current_skills}

        for skill in selected_skills:
            if skill.skill_name not in current_names:
                new_ss = StudentSkill(
                    student_id=student.id,
                    skill_name=skill.skill_name,
                    proficiency_score=50,
                    last_updated=datetime.utcnow(),
                )
                db.session.add(new_ss)

        for ss in current_skills:
            if ss.skill_name not in selected_names:
                db.session.delete(ss)

        db.session.commit()
        logger.info("Skills synced for student_id=%d (%d selected)",
                     student.id, len(selected_skill_ids))
