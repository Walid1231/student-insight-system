from app import create_app
from models import db, Skill, StudentSkill, CareerRequiredSkill
import logging

# Disable distracting logs
logging.getLogger('app').setLevel(logging.ERROR)

def deduplicate_skills():
    app = create_app()
    with app.app_context():
        print("\n=== SKILL CATALOG DEDUPLICATION ===")
        
        # 1. Identify all Skill records
        all_skills = Skill.query.all()
        name_map = {} # name_lower -> [Skills]
        
        for s in all_skills:
            if not s.skill_name: continue
            name_lower = s.skill_name.strip().lower()
            if name_lower not in name_map:
                name_map[name_lower] = []
            name_map[name_lower].append(s)
            
        print(f"Debug: Found {len(name_map)} groups.")
        if "python" in name_map:
            print(f"Debug: 'python' group has {len(name_map['python'])} entries: {[s.id for s in name_map['python']]}")
        
        merged_count = 0
        deleted_count = 0
        
        print(f"Checking {len(name_map)} unique skill names...")
        
        for name, duplicates in name_map.items():
            if len(duplicates) <= 1:
                continue
            
            # Choose the one with the smallest ID as canonical
            duplicates.sort(key=lambda x: x.id)
            canonical = duplicates[0]
            redundant = duplicates[1:]
            
            print(f"Merging '{canonical.skill_name}' (Canonical ID: {canonical.id})")
            
            for redundant_skill in redundant:
                rid = redundant_skill.id
                
                # Update StudentSkill references
                ss_updates = StudentSkill.query.filter_by(skill_id=rid).all()
                for ss in ss_updates:
                    # Check if student already has the canonical one
                    existing_canonical = StudentSkill.query.filter_by(
                        student_id=ss.student_id, skill_id=canonical.id
                    ).first()
                    
                    if existing_canonical:
                        db.session.delete(ss)
                    else:
                        ss.skill_id = canonical.id
                        ss.skill_name = canonical.skill_name
                
                # Update CareerRequiredSkill references
                crs_updates = CareerRequiredSkill.query.filter_by(skill_id=rid).all()
                for crs in crs_updates:
                    # Check for duplicates in the same career
                    existing_canonical = CareerRequiredSkill.query.filter_by(
                        career_id=crs.career_id, skill_id=canonical.id
                    ).first()
                    
                    if existing_canonical:
                        db.session.delete(crs)
                    else:
                        crs.skill_id = canonical.id
                
                # Finally delete the redundant skill record
                db.session.delete(redundant_skill)
                deleted_count += 1
            
            merged_count += 1
            
        db.session.commit()
        print(f"\nDeduplication complete:")
        print(f"  ✓ Skills Merged: {merged_count}")
        print(f"  ✗ Redundant Records Deleted: {deleted_count}")
        print("===================================\n")

if __name__ == "__main__":
    deduplicate_skills()
