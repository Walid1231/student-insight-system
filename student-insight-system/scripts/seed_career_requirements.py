from app import create_app
from models import db, CareerPath, Skill, CareerRequiredSkill
import logging

# Disable distracting logs
logging.getLogger('app').setLevel(logging.ERROR)

# Data source from dashboard/routes.py
DEPT_CAREERS_SKILLS = {
    "Computer Science & Engineering (CSE)": {
        "careers": [
            "Software Developer", "Web Developer", "Mobile App Developer",
            "Data Scientist", "AI / Machine Learning Engineer",
            "Cybersecurity Specialist", "Cloud Engineer", "DevOps Engineer",
            "Game Developer", "Database Administrator", "Systems Analyst",
            "IT Project Manager", "University Lecturer / Researcher",
        ],
        "skills": [
            "Python", "Java", "C++", "JavaScript", "SQL", "HTML/CSS",
            "React", "Node.js", "Git", "Docker", "Linux",
            "Data Structures", "Algorithms", "Machine Learning",
            "Data Analysis", "Cloud Computing", "Web Development",
            "Cybersecurity", "REST APIs", "Databases",
        ],
    },
    "Software Engineering": {
        "careers": [
            "Software Developer", "Web Developer", "Mobile App Developer",
            "Data Scientist", "AI / Machine Learning Engineer",
            "Cybersecurity Specialist", "Cloud Engineer", "DevOps Engineer",
            "Game Developer", "Database Administrator", "Systems Analyst",
            "IT Project Manager", "University Lecturer / Researcher",
        ],
        "skills": [
            "Python", "Java", "C#", "JavaScript", "TypeScript", "SQL",
            "React", "Spring Boot", "Docker", "Kubernetes", "Git",
            "Agile / Scrum", "REST APIs", "System Design", "Testing",
            "Problem Solving",
        ],
    },
    "Electrical & Electronic Engineering (EEE)": {
        "careers": [
            "Electrical Engineer", "Power System Engineer", "Electronics Engineer",
            "Telecommunications Engineer", "Embedded Systems Engineer",
            "Robotics Engineer", "Automation Engineer", "Renewable Energy Engineer",
            "Research Engineer", "Engineering Consultant",
        ],
        "skills": [
            "Circuit Analysis", "MATLAB", "Control Systems", "Embedded Systems",
            "Arduino", "Signal Processing", "Power Systems", "PCB Design",
            "PLC Programming", "AutoCAD Electrical", "VHDL", "Microcontrollers",
            "Communication", "Problem Solving", "Critical Thinking",
        ],
    },
    "Civil Engineering": {
        "careers": [
            "Structural Engineer", "Construction Engineer", "Transportation Engineer",
            "Urban Planner", "Environmental Engineer", "Geotechnical Engineer",
            "Project Manager (Construction)", "Site Engineer", "Government Engineer",
        ],
        "skills": [
            "AutoCAD Civil", "Structural Analysis", "Revit", "Surveying", "GIS",
            "Concrete Design", "Project Scheduling", "Construction Management",
            "Geotechnical Analysis", "ETABS", "Highway Design",
            "Environmental Engineering", "Problem Solving", "Project Management",
        ],
    },
    "Mechanical Engineering": {
        "careers": [
            "Mechanical Engineer", "Manufacturing Engineer", "Automotive Engineer",
            "Aerospace Engineer", "Energy Systems Engineer", "Robotics Engineer",
            "Maintenance Engineer", "Product Design Engineer",
        ],
        "skills": [
            "AutoCAD", "SolidWorks", "ANSYS", "Thermodynamics", "Fluid Mechanics",
            "CNC Machining", "MATLAB", "3D Modeling", "Materials Science",
            "Manufacturing Processes", "FEA Analysis", "Robot Programming",
            "Problem Solving", "Critical Thinking",
        ],
    },
    "Information Technology (IT)": {
        "careers": [
            "IT Support Specialist", "Network Administrator", "Systems Administrator",
            "Cloud Engineer", "Cybersecurity Analyst", "Database Administrator",
            "IT Project Manager", "Business Analyst",
        ],
        "skills": [
            "Networking", "Cybersecurity", "Windows Server", "Linux",
            "Cloud Computing", "Virtualization", "IT Support", "Troubleshooting",
            "Communication", "Problem Solving",
        ],
    },
    "Architecture": {
        "careers": [
            "Architectural Designer", "Urban Designer", "Interior Architect",
            "Landscape Architect", "Sustainable Design Consultant",
            "Project Architect", "BIM Manager",
        ],
        "skills": [
            "AutoCAD", "Revit", "Rhino", "SketchUp", "Architectural Visualization",
            "Urban Planning", "Sustainable Design", "BIM", "3D Modeling",
            "Design Thinking", "Project Management",
        ],
    },
    "Business Administration": {
        "careers": [
            "Business Analyst", "Marketing Manager", "Financial Analyst",
            "Operations Manager", "Human Resources Manager", "Project Manager",
            "Entrepreneur", "Sales Manager", "Supply Chain Manager",
        ],
        "skills": [
            "Business Analysis", "Marketing Strategy", "Financial Modeling",
            "Data Analysis", "Project Management", "Strategic Planning",
            "Leadership", "Communication", "Teamwork", "Problem Solving",
        ],
    },
}

def seed_career_requirements():
    app = create_app()
    with app.app_context():
        print("\n=== SEEDING CAREER REQUIREMENTS ===")
        
        # 1. Ensure all careers exist or find them
        # 2. Map skills
        
        total_mappings = 0
        
        # Build skill map for lookup
        skill_map = {s.skill_name.lower(): s.id for s in Skill.query.all()}
        
        for dept, data in DEPT_CAREERS_SKILLS.items():
            dept_skills = data["skills"]
            dept_careers = data["careers"]
            
            # For each career in this department, map the top relevant skills
            for career_title in dept_careers:
                career = CareerPath.query.filter(CareerPath.title.ilike(f"%{career_title}%")).first()
                if not career:
                    # Create career if missing (using department field_category as fallback)
                    career = CareerPath(title=career_title, field_category=dept)
                    db.session.add(career)
                    db.session.flush()
                
                # Assign up to 8 core skills from the department list as "Required"
                # In a real scenario, this would be curated. Here we take the first 8.
                mapped_count = 0
                for skill_name in dept_skills[:8]:
                    skill_id = skill_map.get(skill_name.lower())
                    if not skill_id:
                        # Create skill if missing
                        new_skill = Skill(skill_name=skill_name, department=dept)
                        db.session.add(new_skill)
                        db.session.flush()
                        skill_id = new_skill.id
                        skill_map[skill_name.lower()] = skill_id
                    
                    # Prevent duplicates
                    existing = CareerRequiredSkill.query.filter_by(
                        career_id=career.id, skill_id=skill_id
                    ).first()
                    if not existing:
                        db.session.add(CareerRequiredSkill(career_id=career.id, skill_id=skill_id))
                        mapped_count += 1
                        total_mappings += 1
                
                # Extra: For specific careers, add specific required skills if not in top 8
                if "Data Scientist" in career_title or "AI" in career_title:
                    for extra in ["Python", "Machine Learning", "Data Analysis"]:
                        sid = skill_map.get(extra.lower())
                        if sid:
                            if not CareerRequiredSkill.query.filter_by(career_id=career.id, skill_id=sid).first():
                                db.session.add(CareerRequiredSkill(career_id=career.id, skill_id=sid))
                                total_mappings += 1
                
                print(f"  ✓ {career.title}: Linked {mapped_count} skills")
        
        db.session.commit()
        print(f"\nSeeding complete. Total mappings created: {total_mappings}")
        print("====================================\n")

if __name__ == "__main__":
    seed_career_requirements()
