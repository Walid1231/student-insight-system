"""
Seed comprehensive CourseCatalog for ALL departments.

Each department gets a realistic set of Core, GED, and Elective courses.
Duplicates are skipped (matched by lowercase course_name).

Usage:
    python seed_courses.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from core.extensions import db
from models import CourseCatalog

# department → [(course_name, course_type, credits), ...]
COURSES = {
    # ══════════════════════════════════════════════════════════
    #  ENGINEERING & TECHNOLOGY
    # ══════════════════════════════════════════════════════════
    "Computer Science": [
        ("Introduction to Computer Science", "Core", 3),
        ("Programming Fundamentals", "Core", 3),
        ("Object-Oriented Programming", "Core", 3),
        ("Data Structures", "Core", 3),
        ("Algorithms", "Core", 3),
        ("Discrete Mathematics", "Core", 3),
        ("Database Systems", "Core", 3),
        ("Operating Systems", "Core", 3),
        ("Computer Networks", "Core", 3),
        ("Software Engineering", "Core", 3),
        ("Computer Architecture", "Core", 3),
        ("Theory of Computation", "Core", 3),
        ("Compiler Design", "Core", 3),
        ("Artificial Intelligence", "Core", 3),
        ("Machine Learning", "Core", 3),
        ("Web Development", "Core", 3),
        ("Mobile Application Development", "Elective", 3),
        ("Cloud Computing", "Elective", 3),
        ("Cybersecurity Fundamentals", "Elective", 3),
        ("Computer Graphics", "Elective", 3),
        ("Natural Language Processing", "Elective", 3),
        ("Deep Learning", "Elective", 3),
        ("Data Mining", "Elective", 3),
        ("Digital Image Processing", "Elective", 3),
        ("Parallel and Distributed Computing", "Elective", 3),
        ("Human-Computer Interaction", "Elective", 3),
        ("Information Security", "Elective", 3),
        ("Software Project Management", "Elective", 3),
        ("Capstone Project I", "Core", 3),
        ("Capstone Project II", "Core", 3),
    ],
    "Data Science": [
        ("Introduction to Data Science", "Core", 3),
        ("Statistical Methods", "Core", 3),
        ("Data Visualization", "Core", 3),
        ("Big Data Analytics", "Core", 3),
        ("Data Warehousing", "Core", 3),
        ("Predictive Analytics", "Core", 3),
        ("Text Analytics", "Elective", 3),
        ("Time Series Analysis", "Elective", 3),
        ("Business Analytics", "Elective", 3),
    ],
    "Electrical & Electronic Engineering (EEE)": [
        ("Circuit Analysis", "Core", 3),
        ("Electronics I", "Core", 3),
        ("Electronics II", "Core", 3),
        ("Digital Logic Design", "Core", 3),
        ("Signals and Systems", "Core", 3),
        ("Electromagnetic Theory", "Core", 3),
        ("Control Systems", "Core", 3),
        ("Power Systems I", "Core", 3),
        ("Power Systems II", "Core", 3),
        ("Communication Systems", "Core", 3),
        ("Microprocessors and Microcontrollers", "Core", 3),
        ("Electrical Machines", "Core", 3),
        ("VLSI Design", "Elective", 3),
        ("Renewable Energy Systems", "Elective", 3),
        ("Digital Signal Processing", "Elective", 3),
        ("Embedded Systems", "Elective", 3),
        ("Antenna and Wave Propagation", "Elective", 3),
        ("Power Electronics", "Elective", 3),
        ("Instrumentation Engineering", "Elective", 3),
        ("Robotics and Automation", "Elective", 3),
        ("EEE Lab I", "Core", 1),
        ("EEE Lab II", "Core", 1),
        ("EEE Capstone Project", "Core", 3),
    ],
    "Civil Engineering": [
        ("Engineering Mechanics", "Core", 3),
        ("Surveying", "Core", 3),
        ("Strength of Materials", "Core", 3),
        ("Structural Analysis I", "Core", 3),
        ("Structural Analysis II", "Core", 3),
        ("Concrete Technology", "Core", 3),
        ("Geotechnical Engineering", "Core", 3),
        ("Fluid Mechanics", "Core", 3),
        ("Hydraulic Engineering", "Core", 3),
        ("Transportation Engineering", "Core", 3),
        ("Environmental Engineering", "Core", 3),
        ("Construction Management", "Core", 3),
        ("Steel Structure Design", "Elective", 3),
        ("Foundation Engineering", "Elective", 3),
        ("Earthquake Engineering", "Elective", 3),
        ("Urban Planning", "Elective", 3),
        ("GIS and Remote Sensing", "Elective", 3),
        ("Water Resources Engineering", "Elective", 3),
        ("Civil Engineering Lab", "Core", 1),
        ("Civil Engineering Capstone", "Core", 3),
    ],
    "Mechanical Engineering": [
        ("Engineering Drawing", "Core", 3),
        ("Thermodynamics", "Core", 3),
        ("Fluid Mechanics & Machinery", "Core", 3),
        ("Mechanics of Solids", "Core", 3),
        ("Manufacturing Processes", "Core", 3),
        ("Machine Design", "Core", 3),
        ("Heat Transfer", "Core", 3),
        ("Internal Combustion Engines", "Core", 3),
        ("Dynamics of Machinery", "Core", 3),
        ("CAD/CAM", "Core", 3),
        ("Industrial Engineering", "Elective", 3),
        ("Automobile Engineering", "Elective", 3),
        ("Refrigeration and Air Conditioning", "Elective", 3),
        ("Finite Element Analysis", "Elective", 3),
        ("Mechatronics", "Elective", 3),
        ("Material Science and Metallurgy", "Elective", 3),
        ("Mechanical Engineering Lab", "Core", 1),
        ("Mechanical Engineering Capstone", "Core", 3),
    ],
    "Information Technology (IT)": [
        ("Introduction to IT", "Core", 3),
        ("Systems Analysis and Design", "Core", 3),
        ("IT Infrastructure", "Core", 3),
        ("Network Security", "Core", 3),
        ("IT Project Management", "Core", 3),
        ("E-Commerce", "Elective", 3),
        ("Enterprise Resource Planning", "Elective", 3),
        ("IT Governance", "Elective", 3),
        ("Digital Forensics", "Elective", 3),
    ],
    "Industrial & Production Engineering (IPE)": [
        ("Work Study and Ergonomics", "Core", 3),
        ("Production Planning and Control", "Core", 3),
        ("Quality Engineering", "Core", 3),
        ("Operations Research", "Core", 3),
        ("Supply Chain Management", "Core", 3),
        ("Lean Manufacturing", "Core", 3),
        ("Safety Engineering", "Elective", 3),
        ("Reliability Engineering", "Elective", 3),
        ("Six Sigma Methodology", "Elective", 3),
        ("IPE Capstone Project", "Core", 3),
    ],

    # ══════════════════════════════════════════════════════════
    #  BUSINESS & MANAGEMENT
    # ══════════════════════════════════════════════════════════
    "Business Administration (BBA)": [
        ("Principles of Management", "Core", 3),
        ("Business Communication", "Core", 3),
        ("Organizational Behavior", "Core", 3),
        ("Financial Management", "Core", 3),
        ("Marketing Management", "Core", 3),
        ("Human Resource Management", "Core", 3),
        ("Business Law", "Core", 3),
        ("Strategic Management", "Core", 3),
        ("Operations Management", "Core", 3),
        ("Business Ethics", "Core", 3),
        ("International Business", "Elective", 3),
        ("Entrepreneurship", "Elective", 3),
        ("Consumer Behavior", "Elective", 3),
        ("Corporate Finance", "Elective", 3),
        ("Leadership and Team Management", "Elective", 3),
        ("BBA Capstone Project", "Core", 3),
    ],
    "Accounting": [
        ("Principles of Accounting", "Core", 3),
        ("Financial Accounting", "Core", 3),
        ("Cost Accounting", "Core", 3),
        ("Management Accounting", "Core", 3),
        ("Auditing and Assurance", "Core", 3),
        ("Taxation", "Core", 3),
        ("Corporate Accounting", "Core", 3),
        ("Accounting Information Systems", "Core", 3),
        ("Advanced Auditing", "Elective", 3),
        ("Forensic Accounting", "Elective", 3),
        ("International Financial Reporting Standards", "Elective", 3),
    ],
    "Marketing": [
        ("Principles of Marketing", "Core", 3),
        ("Digital Marketing", "Core", 3),
        ("Brand Management", "Core", 3),
        ("Advertising and Promotion", "Core", 3),
        ("Sales Management", "Core", 3),
        ("Market Research", "Core", 3),
        ("Social Media Marketing", "Elective", 3),
        ("Services Marketing", "Elective", 3),
        ("Retail Management", "Elective", 3),
    ],
    "Management": [
        ("Introduction to Management", "Core", 3),
        ("Project Management", "Core", 3),
        ("Change Management", "Core", 3),
        ("Negotiation and Conflict Resolution", "Core", 3),
        ("Decision Making", "Core", 3),
        ("Management Information Systems", "Core", 3),
        ("Knowledge Management", "Elective", 3),
        ("Crisis Management", "Elective", 3),
    ],
    "Human Resource Management (HRM)": [
        ("Introduction to HRM", "Core", 3),
        ("Recruitment and Selection", "Core", 3),
        ("Training and Development", "Core", 3),
        ("Compensation Management", "Core", 3),
        ("Performance Management", "Core", 3),
        ("Labor Law", "Core", 3),
        ("Employee Relations", "Core", 3),
        ("HR Analytics", "Elective", 3),
        ("Talent Management", "Elective", 3),
    ],
    "Finance": [
        ("Introduction to Finance", "Core", 3),
        ("Financial Markets and Institutions", "Core", 3),
        ("Investment Analysis", "Core", 3),
        ("Portfolio Management", "Core", 3),
        ("Risk Management", "Core", 3),
        ("Banking and Insurance", "Core", 3),
        ("Financial Derivatives", "Elective", 3),
        ("International Finance", "Elective", 3),
        ("FinTech", "Elective", 3),
    ],

    # ══════════════════════════════════════════════════════════
    #  SCIENCE
    # ══════════════════════════════════════════════════════════
    "Mathematics": [
        ("Calculus I", "Core", 3),
        ("Calculus II", "Core", 3),
        ("Linear Algebra", "Core", 3),
        ("Differential Equations", "Core", 3),
        ("Probability and Statistics", "Core", 3),
        ("Real Analysis", "Core", 3),
        ("Complex Analysis", "Core", 3),
        ("Numerical Methods", "Core", 3),
        ("Abstract Algebra", "Elective", 3),
        ("Topology", "Elective", 3),
        ("Mathematical Modeling", "Elective", 3),
        ("Graph Theory", "Elective", 3),
    ],
    "Physics": [
        ("Classical Mechanics", "Core", 3),
        ("Electricity and Magnetism", "Core", 3),
        ("Optics", "Core", 3),
        ("Thermodynamics and Statistical Mechanics", "Core", 3),
        ("Quantum Mechanics", "Core", 3),
        ("Nuclear Physics", "Core", 3),
        ("Solid State Physics", "Elective", 3),
        ("Astrophysics", "Elective", 3),
        ("Laser Physics", "Elective", 3),
        ("Physics Lab I", "Core", 1),
        ("Physics Lab II", "Core", 1),
    ],
    "Chemistry": [
        ("General Chemistry", "Core", 3),
        ("Organic Chemistry I", "Core", 3),
        ("Organic Chemistry II", "Core", 3),
        ("Inorganic Chemistry", "Core", 3),
        ("Physical Chemistry", "Core", 3),
        ("Analytical Chemistry", "Core", 3),
        ("Biochemistry", "Core", 3),
        ("Environmental Chemistry", "Elective", 3),
        ("Polymer Chemistry", "Elective", 3),
        ("Chemistry Lab I", "Core", 1),
        ("Chemistry Lab II", "Core", 1),
    ],
    "Statistics": [
        ("Introduction to Statistics", "Core", 3),
        ("Regression Analysis", "Core", 3),
        ("Sampling Techniques", "Core", 3),
        ("Design of Experiments", "Core", 3),
        ("Biostatistics", "Core", 3),
        ("Bayesian Statistics", "Elective", 3),
        ("Multivariate Analysis", "Elective", 3),
        ("Survival Analysis", "Elective", 3),
    ],
    "Biotechnology": [
        ("Cell Biology", "Core", 3),
        ("Molecular Biology", "Core", 3),
        ("Genetics", "Core", 3),
        ("Microbiology", "Core", 3),
        ("Bioinformatics", "Core", 3),
        ("Genetic Engineering", "Core", 3),
        ("Immunology", "Elective", 3),
        ("Bioprocess Engineering", "Elective", 3),
        ("Plant Biotechnology", "Elective", 3),
        ("Biotech Lab", "Core", 1),
    ],
    "Environmental Science": [
        ("Introduction to Environmental Science", "Core", 3),
        ("Ecology", "Core", 3),
        ("Environmental Impact Assessment", "Core", 3),
        ("Climate Change and Sustainability", "Core", 3),
        ("Natural Resource Management", "Core", 3),
        ("Waste Management", "Elective", 3),
        ("Environmental Law and Policy", "Elective", 3),
        ("Conservation Biology", "Elective", 3),
    ],

    # ══════════════════════════════════════════════════════════
    #  ARTS & HUMANITIES
    # ══════════════════════════════════════════════════════════
    "English": [
        ("Introduction to English Literature", "Core", 3),
        ("Linguistics", "Core", 3),
        ("Creative Writing", "Core", 3),
        ("Poetry and Prose", "Core", 3),
        ("Shakespeare Studies", "Core", 3),
        ("Modern Literature", "Core", 3),
        ("English Grammar and Composition", "Core", 3),
        ("Literary Criticism", "Core", 3),
        ("Media and Communication Studies", "Elective", 3),
        ("Translation Studies", "Elective", 3),
        ("Discourse Analysis", "Elective", 3),
    ],
    "Bangla": [
        ("Bangla Sahitya Parichay", "Core", 3),
        ("Bangla Kobita", "Core", 3),
        ("Bangla Uponnash", "Core", 3),
        ("Bangla Natak", "Core", 3),
        ("Bhasha Biggan", "Core", 3),
        ("Medieval Bangla Literature", "Core", 3),
        ("Modern Bangla Literature", "Core", 3),
        ("Folklore Studies", "Elective", 3),
        ("Comparative Literature", "Elective", 3),
    ],
    "History": [
        ("Ancient Civilizations", "Core", 3),
        ("History of South Asia", "Core", 3),
        ("Modern World History", "Core", 3),
        ("History of Bangladesh", "Core", 3),
        ("European History", "Core", 3),
        ("Historiography", "Core", 3),
        ("History of the Middle East", "Elective", 3),
        ("Oral History and Documentation", "Elective", 3),
    ],
    "Philosophy": [
        ("Introduction to Philosophy", "Core", 3),
        ("Ethics", "Core", 3),
        ("Logic", "Core", 3),
        ("Political Philosophy", "Core", 3),
        ("Epistemology", "Core", 3),
        ("Aesthetics", "Core", 3),
        ("Philosophy of Mind", "Elective", 3),
        ("Existentialism", "Elective", 3),
        ("Buddhist Philosophy", "Elective", 3),
    ],

    # ══════════════════════════════════════════════════════════
    #  SOCIAL SCIENCE
    # ══════════════════════════════════════════════════════════
    "Economics": [
        ("Microeconomics", "Core", 3),
        ("Macroeconomics", "Core", 3),
        ("Econometrics", "Core", 3),
        ("Development Economics", "Core", 3),
        ("International Economics", "Core", 3),
        ("Public Finance", "Core", 3),
        ("Monetary Economics", "Elective", 3),
        ("Health Economics", "Elective", 3),
        ("Labor Economics", "Elective", 3),
        ("Environmental Economics", "Elective", 3),
    ],
    "Sociology": [
        ("Introduction to Sociology", "Core", 3),
        ("Social Research Methods", "Core", 3),
        ("Social Stratification", "Core", 3),
        ("Gender Studies", "Core", 3),
        ("Urban Sociology", "Core", 3),
        ("Sociology of Education", "Core", 3),
        ("Rural Sociology", "Elective", 3),
        ("Criminology", "Elective", 3),
        ("Medical Sociology", "Elective", 3),
    ],
    "Political Science": [
        ("Introduction to Political Science", "Core", 3),
        ("Comparative Politics", "Core", 3),
        ("Political Theory", "Core", 3),
        ("International Relations", "Core", 3),
        ("Public Policy", "Core", 3),
        ("South Asian Politics", "Core", 3),
        ("Governance and Institutions", "Elective", 3),
        ("Electoral Systems", "Elective", 3),
        ("Political Economy", "Elective", 3),
    ],
    "International Relations": [
        ("Theories of International Relations", "Core", 3),
        ("Global Governance", "Core", 3),
        ("Foreign Policy Analysis", "Core", 3),
        ("Conflict and Peace Studies", "Core", 3),
        ("International Law", "Core", 3),
        ("International Political Economy", "Elective", 3),
        ("Diplomacy", "Elective", 3),
        ("Regional Security", "Elective", 3),
    ],
    "Public Administration": [
        ("Introduction to Public Administration", "Core", 3),
        ("Public Policy Analysis", "Core", 3),
        ("Governance and Development", "Core", 3),
        ("Administrative Law", "Core", 3),
        ("Local Government", "Core", 3),
        ("Public Sector Management", "Elective", 3),
        ("NGO Management", "Elective", 3),
    ],

    # ══════════════════════════════════════════════════════════
    #  HEALTH & PHARMACY
    # ══════════════════════════════════════════════════════════
    "Pharmacy": [
        ("Pharmaceutics I", "Core", 3),
        ("Pharmaceutics II", "Core", 3),
        ("Pharmacology I", "Core", 3),
        ("Pharmacology II", "Core", 3),
        ("Pharmaceutical Chemistry", "Core", 3),
        ("Medicinal Chemistry", "Core", 3),
        ("Clinical Pharmacy", "Core", 3),
        ("Hospital Pharmacy", "Core", 3),
        ("Drug Design", "Elective", 3),
        ("Biopharmaceutics", "Elective", 3),
        ("Quality Assurance in Pharmacy", "Elective", 3),
        ("Pharmacy Lab I", "Core", 1),
        ("Pharmacy Lab II", "Core", 1),
    ],
    "Public Health": [
        ("Introduction to Public Health", "Core", 3),
        ("Epidemiology", "Core", 3),
        ("Health Promotion and Education", "Core", 3),
        ("Environmental Health", "Core", 3),
        ("Maternal and Child Health", "Core", 3),
        ("Health Systems Management", "Core", 3),
        ("Nutrition and Public Health", "Elective", 3),
        ("Communicable Disease Control", "Elective", 3),
        ("Global Health", "Elective", 3),
    ],
    "Nursing": [
        ("Fundamentals of Nursing", "Core", 3),
        ("Medical-Surgical Nursing", "Core", 3),
        ("Pediatric Nursing", "Core", 3),
        ("Obstetric Nursing", "Core", 3),
        ("Psychiatric Nursing", "Core", 3),
        ("Community Health Nursing", "Core", 3),
        ("Nursing Research", "Core", 3),
        ("Critical Care Nursing", "Elective", 3),
        ("Geriatric Nursing", "Elective", 3),
        ("Nursing Clinical Practicum", "Core", 3),
    ],

    # ══════════════════════════════════════════════════════════
    #  LAW
    # ══════════════════════════════════════════════════════════
    "Law (LLB)": [
        ("Introduction to Law", "Core", 3),
        ("Constitutional Law", "Core", 3),
        ("Criminal Law", "Core", 3),
        ("Contract Law", "Core", 3),
        ("Law of Torts", "Core", 3),
        ("Family Law", "Core", 3),
        ("Property Law", "Core", 3),
        ("Corporate Law", "Core", 3),
        ("International Humanitarian Law", "Core", 3),
        ("Evidence Law", "Core", 3),
        ("Legal Research and Writing", "Core", 3),
        ("Environmental Law", "Elective", 3),
        ("Cyber Law", "Elective", 3),
        ("Intellectual Property Law", "Elective", 3),
        ("Moot Court Practice", "Core", 3),
    ],

    # ══════════════════════════════════════════════════════════
    #  GED COURSES (shared across departments)
    # ══════════════════════════════════════════════════════════
    "General": [
        ("English Composition", "GED", 3),
        ("Critical Thinking and Writing", "GED", 3),
        ("Public Speaking", "GED", 3),
        ("Introduction to Psychology", "GED", 3),
        ("Introduction to Sociology", "GED", 3),
        ("Bangladesh Studies", "GED", 3),
        ("History of Science", "GED", 3),
        ("World Civilizations", "GED", 3),
        ("Art Appreciation", "GED", 3),
        ("Music Appreciation", "GED", 3),
        ("Environmental Studies", "GED", 3),
        ("Health and Wellness", "GED", 3),
        ("Fundamentals of Economics", "GED", 3),
        ("Introduction to Philosophy", "GED", 3),
        ("Academic Writing", "GED", 3),
        ("Technical English", "GED", 3),
        ("Ethics and Society", "GED", 3),
        ("Bangla Language and Culture", "GED", 3),
        ("Physical Education", "GED", 1),
        ("University Seminar", "GED", 1),
    ],
}


def run():
    app = create_app()
    with app.app_context():
        added = 0
        skipped = 0

        # Build a set of existing course names (lowercase) for fast lookup
        existing = {c.course_name.lower() for c in CourseCatalog.query.all()}

        for dept, courses in COURSES.items():
            for course_name, course_type, credits in courses:
                if course_name.lower() in existing:
                    skipped += 1
                    continue

                db.session.add(CourseCatalog(
                    course_name=course_name,
                    department=dept,
                    course_type=course_type,
                    credit_value=credits,
                ))
                existing.add(course_name.lower())
                added += 1

        db.session.commit()
        total = CourseCatalog.query.count()

        print(f"\n{'='*60}")
        print(f"  Course Catalog Seeding Complete")
        print(f"{'='*60}")
        print(f"  New courses added:    {added}")
        print(f"  Duplicates skipped:   {skipped}")
        print(f"  Total in catalog:     {total}")
        print()


if __name__ == "__main__":
    run()
