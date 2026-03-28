from app import create_app
from models import db, Skill, StudentSkill, CareerRequiredSkill, StudentProfile, CareerPath
import logging

# Disable distracting logs
logging.getLogger('app').setLevel(logging.ERROR)

def ultimate_skill_sync():
    app = create_app()
    with app.app_context():
        print("\n=== ULTIMATE SKILL SYNCHRONIZATION ===")
        
        # 1. Map canonical IDs by Name (lowercase)
        all_skills = Skill.query.all()
        canonical_map = {} # name_lower -> canonical_skill_record
        
        # Sort by ID so the earliest ID becomes canonical
        all_skills.sort(key=lambda x: x.id)
        
        unique_names = 0
        for s in all_skills:
            name_lower = s.skill_name.strip().lower()
            if name_lower not in canonical_map:
                canonical_map[name_lower] = s
                unique_names += 1
                print(f"Canonical: '{s.skill_name}' -> ID {s.id}")
        
        # 2. Update StudentSkill References
        print("\nSyncing Student Records...")
        students_updated = 0
        for ss in StudentSkill.query.all():
            name_lower = ss.skill_name.strip().lower()
            canonical = canonical_map.get(name_lower)
            if canonical and ss.skill_id != canonical.id:
                # Update link
                # Note: Not merging duplicate StudentSkill entries for same user
                # just to keep it simple, but usually one student shouldn't have ID 1 and ID 11
                ss.skill_id = canonical.id
                ss.skill_name = canonical.skill_name
                students_updated += 1
        
        # 3. Update CareerRequiredSkill References
        print("Syncing Career Requirements...")
        career_reqs_updated = 0
        for crs in CareerRequiredSkill.query.all():
            # Join with Skill to see the CURRENT name
            skill = Skill.query.get(crs.skill_id)
            if skill:
                name_lower = skill.skill_name.strip().lower()
                canonical = canonical_map.get(name_lower)
                if canonical and crs.skill_id != canonical.id:
                    # Update link
                    # Check if already linked to canonical in this career (prevent duplicate PK)
                    existing = CareerRequiredSkill.query.filter_by(
                        career_id=crs.career_id, skill_id=canonical.id
                    ).first()
                    if existing:
                        db.session.delete(crs)
                    else:
                        crs.skill_id = canonical.id
                    career_reqs_updated += 1
        
        # 4. Cleanup redundant Skill records
        print("Deleting redundant Skills...")
        deleted_count = 0
        for s in all_skills:
            name_lower = s.skill_name.strip().lower()
            canonical = canonical_map[name_lower]
            if s.id != canonical.id:
                db.session.delete(s)
                deleted_count += 1
        
        db.session.commit()
        print(f"\nSynchronization Complete:")
        print(f"  ✓ Unique Skills Maintained: {unique_names}")
        print(f"  ✓ Redundant Records Deleted: {deleted_count}")
        print(f"  ✓ Student Links Updated: {students_updated}")
        print(f"  ✓ Career Links Updated: {career_reqs_updated}")
        print("===================================\n")

        # 5. TEST: AI ENGINEER COMPATIBILITY CHECK
        ahmed = StudentProfile.query.filter_by(full_name='Ahmed Al-Rashid').first()
        career = CareerPath.query.filter(CareerPath.title.ilike('%AI%')).first()
        
        if ahmed and career:
            a_skill_ids = [ss.skill_id for ss in StudentSkill.query.filter_by(student_id=ahmed.id).all()]
            req_skill_ids = [r.skill_id for r in CareerRequiredSkill.query.filter_by(career_id=career.id).all()]
            matches = set(a_skill_ids).intersection(set(req_skill_ids))
            
            print(f"POST-SYNC TEST for {ahmed.full_name} vs {career.title}:")
            print(f"  Student IDs: {a_skill_ids}")
            print(f"  Required IDs: {req_skill_ids}")
            print(f"  Matches: {len(matches)} / {len(req_skill_ids)}")
            if len(req_skill_ids) > 0:
                print(f"  Match Percentage: {int(len(matches)/len(req_skill_ids)*100)}%")

if __name__ == "__main__":
    ultimate_skill_sync()
