"""
Skill tracking and action plan service.

Extracted from routes.py: api_update_skill(), api_get_skill_history(),
api_get_action_plans(), api_generate_action_plan(), api_complete_action_plan().
"""

import logging
from datetime import datetime

from core.errors import NotFoundError
from core.extensions import db
from models import (
    StudentProfile, StudentSkill, StudentSkillProgress, ActionPlan,
)

logger = logging.getLogger(__name__)


class SkillService:
    """Skill tracking, risk scoring, and AI action plans — HTTP-unaware."""

    @staticmethod
    def _get_student(user_id):
        student = StudentProfile.query.filter_by(user_id=int(user_id)).first()
        if not student:
            raise NotFoundError("Student not found")
        return student

    @staticmethod
    def update_skill(user_id: str, skill_name: str, proficiency: int) -> dict:
        """Update or create a skill with proficiency score."""
        student = SkillService._get_student(user_id)

        skill = StudentSkill.query.filter_by(
            student_id=student.id, skill_name=skill_name
        ).first()
        if not skill:
            skill = StudentSkill(student_id=student.id, skill_name=skill_name)
            db.session.add(skill)
            db.session.flush()

        if not skill.skill_id:
            from models import Skill as SkillModel
            master = SkillModel.query.filter(
                db.func.lower(SkillModel.skill_name) == skill_name.lower()
            ).first()
            if master:
                skill.skill_id = master.id
                skill.skill_name = master.skill_name

        skill.proficiency_score = proficiency
        skill.last_updated = datetime.utcnow()

        # Calculate risk: simple inverse of proficiency weighted by CGPA
        cgpa = student.current_cgpa or 2.0
        risk = max(0, min(1.0, (100 - proficiency) / 100 * (4.0 - cgpa) / 4.0 + 0.1))
        skill.risk_score = round(risk, 2)

        # Log history
        history = StudentSkillProgress(
            student_skill_id=skill.id,
            proficiency_score=skill.proficiency_score,
            risk_score=skill.risk_score,
            date=datetime.utcnow().date(),
        )
        db.session.add(history)
        db.session.commit()

        logger.info("Skill '%s' updated for student_id=%d", skill_name, student.id)
        return {
            "skill": skill.skill_name,
            "proficiency": skill.proficiency_score,
            "risk": skill.risk_score,
        }

    @staticmethod
    def get_skill_history(user_id: str) -> list[dict]:
        """Get all skills with their progress history for a student."""
        student = SkillService._get_student(user_id)

        skills = StudentSkill.query.filter_by(student_id=student.id).all()
        data = []
        for skill in skills:
            history = StudentSkillProgress.query.filter_by(
                student_skill_id=skill.id
            ).order_by(StudentSkillProgress.date).all()
            data.append({
                "skill": skill.skill_name,
                "current_score": skill.proficiency_score,
                "current_risk": skill.risk_score,
                "history": [
                    {"date": h.date.isoformat(), "score": h.proficiency_score}
                    for h in history
                ],
            })
        return data

    @staticmethod
    def get_action_plans(user_id: str) -> list[dict]:
        """Get all action plans for a student."""
        student = SkillService._get_student(user_id)

        plans = ActionPlan.query.filter_by(
            student_id=student.id
        ).order_by(ActionPlan.status.desc(), ActionPlan.due_date).all()

        return [{
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "status": p.status,
            "due_date": p.due_date.isoformat() if p.due_date else None,
        } for p in plans]

    @staticmethod
    def generate_action_plan(user_id: str, ai_service) -> dict:
        """Generate AI action plans for the weakest skill."""
        student = SkillService._get_student(user_id)

        weak_skills = StudentSkill.query.filter(
            StudentSkill.student_id == student.id,
            StudentSkill.risk_score > 0.5,
        ).all()

        if not weak_skills:
            return {"success": True, "created": [], "msg": "No high-risk skills found."}

        target_skill = weak_skills[0]

        prompt = f"""
        Generate a JSON list of 3 specific, actionable tasks for a student to improve their {target_skill.skill_name} skill
        from level {target_skill.proficiency_score}/100 to {target_skill.proficiency_score + 20}/100.
        Format: [{{"title": "Task Title", "description": "Details", "days_to_complete": 5}}]
        """

        tasks = ai_service.generate_json(prompt)

        created_plans = []
        for task in tasks:
            plan = ActionPlan(
                student_id=student.id,
                skill_id=target_skill.id,
                title=task.get('title'),
                description=task.get('description'),
                status='pending',
                due_date=datetime.utcnow().date(),
            )
            db.session.add(plan)
            created_plans.append(plan.title)

        db.session.commit()
        logger.info("Action plans generated for student_id=%d, skill=%s",
                     student.id, target_skill.skill_name)
        return {"success": True, "created": created_plans}

    @staticmethod
    def complete_action_plan(user_id: str, plan_id: int) -> dict:
        """Mark an action plan as completed and boost skill proficiency."""
        student = SkillService._get_student(user_id)

        plan = ActionPlan.query.get(plan_id)
        if not plan or plan.student_id != student.id:
            raise NotFoundError("Plan not found")

        plan.status = 'completed'
        plan.completed_at = datetime.utcnow()

        new_score = None
        if plan.skill:
            plan.skill.proficiency_score = min(100, plan.skill.proficiency_score + 2)
            cgpa = student.current_cgpa or 2.0
            prof = plan.skill.proficiency_score
            plan.skill.risk_score = round(
                max(0, min(1.0, (100 - prof) / 100 * (4.0 - cgpa) / 4.0 + 0.1)), 2
            )
            new_score = plan.skill.proficiency_score

        db.session.commit()
        logger.info("Action plan %d completed", plan_id)
        return {"new_score": new_score}
