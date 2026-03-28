from app import create_app
from models import db, StudentSkill, Skill
import logging

# Disable distracting logs
logging.getLogger('app').setLevel(logging.ERROR)

def migrate_skill_ids():
    app = create_app()
    with app.app_context():
        print("\n=== LEGACY SKILL DATA MIGRATION ===")
        
        # Get all StudentSkills that haven't been linked yet
        legacy_skills = StudentSkill.query.filter(StudentSkill.skill_id == None).all()
        print(f"Found {len(legacy_skills)} legacy skills to process.")
        
        updated_count = 0
        failed_count = 0
        
        # Cache master skills for faster lookup
        master_skills = {s.skill_name.lower(): s for s in Skill.query.all()}
        
        for ss in legacy_skills:
            name_lower = ss.skill_name.lower()
            if name_lower in master_skills:
                master = master_skills[name_lower]
                ss.skill_id = master.id
                ss.skill_name = master.skill_name  # sync casing
                updated_count += 1
            else:
                # If no master exists, we could create one or leave as is
                # For now, let's leave as is (custom skill)
                failed_count += 1
        
        db.session.commit()
        print(f"Update complete:")
        print(f"  ✓ Linked to Master: {updated_count}")
        print(f"  ✗ Remains Custom: {failed_count}")
        print("===================================\n")

if __name__ == "__main__":
    migrate_skill_ids()
