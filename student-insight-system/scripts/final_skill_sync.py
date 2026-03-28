from app import create_app
from models import db, Skill, StudentSkill, CareerRequiredSkill
import logging

# Disable distracting logs
logging.getLogger('app').setLevel(logging.ERROR)

def final_skill_sync():
    app = create_app()
    with app.app_context():
        print("\n=== FINAL SKILL SYNCHRONIZATION ===")
        
        # 1. Map canonical IDs by Name (lowercase)
        all_skills = Skill.query.all()
        canonical_map = {} # name_lower -> first_id
        
        # Sort by ID so the earliest ID becomes canonical
        all_skills.sort(key=lambda x: x.id)
        
        for s in all_skills:
            name_lower = s.skill_name.strip().lower()
            if name_lower not in canonical_map:
                canonical_map[name_lower] = s.id
                print(f"Canonical: '{s.skill_name}' -> ID {s.id}")
        
        # 2. Update StudentSkill References
        print("\nSyncing Student Records...")
        students_updated = 0
        for ss in StudentSkill.query.all():
            name_lower = ss.skill_name.strip().lower()
            canonical_id = canonical_map.get(name_lower)
            if canonical_id and ss.skill_id != canonical_id:
                # Merge if duplicate
                existing = StudentSkill.query.filter_by(
                    student_id=ss.student_id, skill_id=canonical_id
                ).first()
                if existing:
                    db.session.delete(ss)
                else:
                    ss.skill_id = canonical_id
                    ss.skill_name = Skill.query.get(canonical_id).skill_name
                students_updated += 1
        
        # 3. Update CareerRequiredSkill References
        print("Syncing Career Requirements...")
        career_reqs_updated = 0
        for crs in CareerRequiredSkill.query.all():
            skill = Skill.query.get(crs.skill_id)
            if skill:
                name_lower = skill.skill_name.strip().lower()
                canonical_id = canonical_map.get(name_lower)
                if canonical_id and crs.skill_id != canonical_id:
                    # Merge if duplicate
                    existing = CareerRequiredSkill.query.filter_by(
                        career_id=crs.career_id, skill_id=canonical_id
                    ).first()
                    if existing:
                        db.session.delete(crs)
                    else:
                        crs.skill_id = canonical_id
                    career_reqs_updated += 1
        
        # 4. Delete Redundant Skills
        print("Cleaning up Skill table...")
        deleted_count = 0
        deleted_ids = []
        for s in all_skills:
            name_lower = s.skill_name.strip().lower()
            if s.id != canonical_map[name_lower]:
                db.session.delete(s)
                deleted_ids.append(s.id)
                deleted_count += 1
        
        db.session.commit()
        print(f"\nSynchronization Complete:")
        print(f"  ✓ Total Unique Skills: {len(canonical_map)}")
        print(f"  ✓ Redundant Records Deleted: {deleted_count}")
        print(f"  ✓ Records Updated: {students_updated + career_reqs_updated}")
        print("===================================\n")

if __name__ == "__main__":
    final_skill_sync()
