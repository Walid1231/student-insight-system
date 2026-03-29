"""
Seed career → skill mappings for ALL career paths.

For each career we define 4-8 required skills.
Skills are looked up (or created) in the master `skills` table,
then linked via `career_required_skills`.

Usage:
    python seed_career_skills.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from core.extensions import db
from models import CareerPath, CareerRequiredSkill, Skill

# ─── career_title  →  [skill_name, ...]  ──────────────────────
CAREER_SKILLS = {
    # ══ Computer Science ══
    "Software Engineer": [
        "Python", "Java", "Data Structures", "Algorithms", "Git",
        "Software Architecture", "REST API", "SQL"
    ],
    "Data Scientist": [
        "Python", "Machine Learning", "Statistics", "Data Visualization",
        "SQL", "TensorFlow", "Pandas", "R"
    ],
    "Machine Learning Engineer": [
        "Python", "Machine Learning", "Deep Learning", "TensorFlow",
        "PyTorch", "Data Preprocessing", "Linear Algebra", "Statistics"
    ],
    "Full Stack Developer": [
        "JavaScript", "React", "Node.js", "HTML/CSS", "REST API",
        "SQL", "Git", "TypeScript"
    ],
    "Cybersecurity Analyst": [
        "Network Security", "Ethical Hacking", "Linux", "Firewalls",
        "Incident Response", "Cryptography", "SIEM Tools", "Risk Assessment"
    ],
    "AI Researcher": [
        "Python", "Deep Learning", "Natural Language Processing",
        "Computer Vision", "Research Methodology", "Linear Algebra",
        "TensorFlow", "PyTorch"
    ],
    "Cloud Engineer": [
        "AWS", "Azure", "Docker", "Kubernetes", "Linux",
        "Networking", "Terraform", "CI/CD"
    ],
    "DevOps Engineer": [
        "Docker", "Kubernetes", "CI/CD", "Linux", "AWS",
        "Git", "Jenkins", "Ansible"
    ],
    "Mobile App Developer": [
        "Kotlin", "Swift", "React Native", "Flutter", "REST API",
        "UI/UX Design", "Git", "Firebase"
    ],
    "Database Administrator": [
        "SQL", "PostgreSQL", "MySQL", "Database Design", "Performance Tuning",
        "Backup & Recovery", "NoSQL", "Data Modeling"
    ],

    # ══ Data Science ══
    "Data Engineer": [
        "Python", "SQL", "Apache Spark", "ETL Pipelines", "AWS",
        "Data Warehousing", "Kafka", "Airflow"
    ],
    "Business Intelligence Analyst": [
        "SQL", "Power BI", "Tableau", "Data Visualization", "Excel",
        "Data Warehousing", "Statistics", "Python"
    ],

    # ══ Electrical & Electronic Engineering (EEE) ══
    "Electrical Engineer": [
        "Circuit Design", "Power Systems", "MATLAB", "AutoCAD",
        "Control Systems", "Electrical Safety", "PCB Design", "PLC Programming"
    ],
    "Telecommunications Engineer": [
        "Signal Processing", "Networking", "5G Technology", "RF Engineering",
        "MATLAB", "Antenna Design", "Fiber Optics", "Embedded Systems"
    ],
    "Electronics Design Engineer": [
        "PCB Design", "Embedded Systems", "VHDL/Verilog", "Circuit Design",
        "Microcontrollers", "MATLAB", "Soldering", "Signal Processing"
    ],
    "Power Systems Engineer": [
        "Power Systems", "MATLAB", "Circuit Design", "Electrical Safety",
        "SCADA", "AutoCAD", "Control Systems", "Renewable Energy"
    ],
    "Control Systems Engineer": [
        "Control Systems", "MATLAB", "PLC Programming", "Automation",
        "Robotics", "Embedded Systems", "Signal Processing", "Python"
    ],
    "Automation Engineer": [
        "PLC Programming", "SCADA", "Automation", "Robotics",
        "Embedded Systems", "Python", "Control Systems", "Industrial IoT"
    ],
    "Renewable Energy Engineer": [
        "Renewable Energy", "Solar Panel Design", "Power Systems",
        "MATLAB", "AutoCAD", "Energy Storage", "Electrical Safety", "Sustainability"
    ],
    "Research Engineer": [
        "MATLAB", "Research Methodology", "Signal Processing", "Python",
        "Data Analysis", "Technical Writing", "Embedded Systems", "Circuit Design"
    ],
    "Engineering Consultant": [
        "Project Management", "Technical Writing", "AutoCAD",
        "Risk Assessment", "Communication", "Problem Solving", "MATLAB", "Leadership"
    ],

    # ══ Civil Engineering ══
    "Structural Engineer": [
        "Structural Analysis", "AutoCAD", "ETABS", "SAP2000",
        "Concrete Design", "Steel Design", "MATLAB", "Project Management"
    ],
    "Construction Engineer": [
        "Construction Management", "AutoCAD", "Project Management",
        "Cost Estimation", "Safety Management", "Concrete Technology", "Scheduling", "Quality Control"
    ],
    "Transportation Engineer": [
        "Traffic Engineering", "AutoCAD", "GIS", "Urban Planning",
        "Transportation Modeling", "Data Analysis", "Highway Design", "Project Management"
    ],
    "Urban Planner": [
        "Urban Planning", "GIS", "AutoCAD", "Sustainability",
        "Policy Analysis", "Community Engagement", "Data Analysis", "Communication"
    ],
    "Environmental Engineer": [
        "Environmental Impact Assessment", "Water Treatment", "AutoCAD",
        "Sustainability", "Waste Management", "GIS", "Data Analysis", "Environmental Law"
    ],
    "Geotechnical Engineer": [
        "Soil Mechanics", "Foundation Design", "AutoCAD", "MATLAB",
        "Geotechnical Investigation", "Structural Analysis", "Data Analysis", "Risk Assessment"
    ],
    "Project Manager (Construction)": [
        "Project Management", "Cost Estimation", "Scheduling",
        "Risk Management", "AutoCAD", "Leadership", "Communication", "Safety Management"
    ],
    "Site Engineer": [
        "Construction Management", "AutoCAD", "Surveying",
        "Quality Control", "Safety Management", "Concrete Technology", "Project Management", "Communication"
    ],
    "Government Engineer": [
        "AutoCAD", "Project Management", "Policy Analysis",
        "Environmental Law", "Communication", "Technical Writing", "Data Analysis", "Leadership"
    ],

    # ══ Mechanical Engineering ══
    "Mechanical Engineer": [
        "SolidWorks", "AutoCAD", "Thermodynamics", "Material Science",
        "MATLAB", "Manufacturing Processes", "Finite Element Analysis", "3D Printing"
    ],
    "Manufacturing Engineer": [
        "Manufacturing Processes", "Lean Manufacturing", "Six Sigma",
        "Quality Control", "AutoCAD", "SolidWorks", "Process Optimization", "CNC Programming"
    ],
    "Automotive Engineer": [
        "Automotive Design", "SolidWorks", "Thermodynamics",
        "Material Science", "MATLAB", "Engine Systems", "CAD/CAM", "Finite Element Analysis"
    ],
    "Aerospace Engineer": [
        "Aerodynamics", "MATLAB", "SolidWorks", "Finite Element Analysis",
        "Propulsion Systems", "Material Science", "Control Systems", "Flight Dynamics"
    ],
    "Energy Systems Engineer": [
        "Thermodynamics", "Renewable Energy", "MATLAB", "Power Systems",
        "Energy Storage", "AutoCAD", "Sustainability", "Process Optimization"
    ],
    "Maintenance Engineer": [
        "Maintenance Management", "Failure Analysis", "SolidWorks",
        "Safety Management", "PLC Programming", "Troubleshooting", "AutoCAD", "Quality Control"
    ],
    "Product Design Engineer": [
        "SolidWorks", "3D Printing", "Material Science", "User Research",
        "Prototyping", "AutoCAD", "Design Thinking", "Manufacturing Processes"
    ],

    # ══ Information Technology (IT) ══
    "IT Support Specialist": [
        "Windows Administration", "Networking", "Troubleshooting",
        "Help Desk Management", "Linux", "Active Directory", "Customer Service", "Hardware Maintenance"
    ],
    "Network Administrator": [
        "Networking", "Cisco", "Firewalls", "Linux",
        "Windows Administration", "VPN", "DNS/DHCP", "Network Monitoring"
    ],
    "Systems Administrator": [
        "Linux", "Windows Administration", "Networking",
        "Virtualization", "Active Directory", "Shell Scripting", "Backup & Recovery", "Cloud Computing"
    ],

    # ══ Industrial & Production Engineering (IPE) ══
    "Industrial Engineer": [
        "Lean Manufacturing", "Six Sigma", "Process Optimization",
        "AutoCAD", "Statistics", "Supply Chain Management", "Quality Control", "Operations Research"
    ],
    "Production Manager": [
        "Production Planning", "Lean Manufacturing", "Quality Control",
        "Safety Management", "Leadership", "Supply Chain Management", "Process Optimization", "ERP Systems"
    ],
    "Quality Assurance Engineer": [
        "Quality Control", "Six Sigma", "ISO Standards",
        "Statistical Process Control", "Root Cause Analysis", "Auditing", "Documentation", "Testing"
    ],
    "Supply Chain Analyst": [
        "Supply Chain Management", "Data Analysis", "Excel",
        "ERP Systems", "Logistics", "Forecasting", "SQL", "Power BI"
    ],
    "Operations Manager": [
        "Operations Management", "Lean Manufacturing", "Leadership",
        "Budgeting", "Supply Chain Management", "Process Optimization", "Quality Control", "Communication"
    ],
    "Process Improvement Engineer": [
        "Six Sigma", "Lean Manufacturing", "Process Optimization",
        "Data Analysis", "Root Cause Analysis", "Statistics", "Project Management", "Kaizen"
    ],

    # ══ Business Administration (BBA) ══
    "Business Manager": [
        "Business Strategy", "Leadership", "Financial Analysis",
        "Communication", "Project Management", "Marketing", "Operations Management", "Negotiation"
    ],
    "Marketing Manager": [
        "Marketing Strategy", "Digital Marketing", "Market Research",
        "Brand Management", "Communication", "Data Analysis", "Leadership", "Social Media"
    ],
    "Financial Analyst": [
        "Financial Modeling", "Excel", "Financial Reporting",
        "Data Analysis", "Accounting", "Valuation", "SQL", "Power BI"
    ],
    "HR Manager": [
        "Human Resource Management", "Recruitment", "Employee Relations",
        "Communication", "Leadership", "Labor Law", "Performance Management", "Training & Development"
    ],
    "Business Consultant": [
        "Business Strategy", "Financial Analysis", "Communication",
        "Problem Solving", "Data Analysis", "Project Management", "Presentation", "Market Research"
    ],
    "Entrepreneur / Startup Founder": [
        "Business Strategy", "Leadership", "Marketing",
        "Financial Modeling", "Product Management", "Communication", "Fundraising", "Lean Startup"
    ],
    "Supply Chain Manager": [
        "Supply Chain Management", "Logistics", "ERP Systems",
        "Negotiation", "Data Analysis", "Communication", "Leadership", "Budgeting"
    ],
    "Corporate Executive": [
        "Leadership", "Business Strategy", "Financial Analysis",
        "Communication", "Strategic Planning", "Corporate Governance", "Negotiation", "Decision Making"
    ],

    # ══ Accounting ══
    "Accountant": [
        "Accounting", "Financial Reporting", "Taxation", "Excel",
        "Auditing", "Bookkeeping", "ERP Systems", "Compliance"
    ],
    "Auditor": [
        "Auditing", "Accounting", "Financial Reporting", "Risk Assessment",
        "Compliance", "Excel", "Internal Controls", "Communication"
    ],
    "Investment Banker": [
        "Financial Modeling", "Valuation", "Mergers & Acquisitions",
        "Excel", "Accounting", "Communication", "Presentation", "Financial Markets"
    ],
    "Tax Consultant": [
        "Taxation", "Accounting", "Financial Reporting", "Compliance",
        "Tax Planning", "Excel", "Communication", "Business Law"
    ],
    "Chartered Accountant": [
        "Accounting", "Auditing", "Taxation", "Financial Reporting",
        "Compliance", "Business Law", "Excel", "Corporate Governance"
    ],
    "Risk Analyst": [
        "Risk Assessment", "Financial Modeling", "Data Analysis",
        "Statistics", "Excel", "Compliance", "Communication", "Python"
    ],
    "Banking Officer": [
        "Banking Operations", "Financial Analysis", "Customer Service",
        "Compliance", "Communication", "Excel", "Risk Assessment", "Sales"
    ],

    # ══ Marketing ══
    "Digital Marketing Specialist": [
        "Digital Marketing", "SEO", "Google Analytics", "Social Media",
        "Content Marketing", "PPC Advertising", "Email Marketing", "Data Analysis"
    ],
    "Brand Manager": [
        "Brand Management", "Marketing Strategy", "Market Research",
        "Communication", "Creative Thinking", "Data Analysis", "Social Media", "Leadership"
    ],
    "Content Strategist": [
        "Content Marketing", "SEO", "Copywriting", "Social Media",
        "Data Analysis", "Communication", "Content Management Systems", "Google Analytics"
    ],
    "SEO Specialist": [
        "SEO", "Google Analytics", "Content Marketing", "HTML/CSS",
        "Keyword Research", "Link Building", "Data Analysis", "Technical SEO"
    ],
    "Social Media Manager": [
        "Social Media", "Content Marketing", "Communication",
        "Digital Marketing", "Data Analysis", "Creative Thinking", "Video Editing", "Copywriting"
    ],
    "Market Research Analyst": [
        "Market Research", "Data Analysis", "Statistics", "Survey Design",
        "Excel", "SPSS", "Communication", "Presentation"
    ],

    # ══ Management ══
    "Project Manager": [
        "Project Management", "Agile/Scrum", "Leadership",
        "Communication", "Risk Management", "Budgeting", "Scheduling", "Stakeholder Management"
    ],
    "Consultant": [
        "Business Strategy", "Communication", "Problem Solving",
        "Data Analysis", "Presentation", "Financial Analysis", "Project Management", "Research Methodology"
    ],
    "General Manager": [
        "Leadership", "Operations Management", "Business Strategy",
        "Financial Analysis", "Communication", "Decision Making", "Strategic Planning", "Team Management"
    ],
    "Team Lead": [
        "Leadership", "Communication", "Project Management",
        "Conflict Resolution", "Team Management", "Problem Solving", "Time Management", "Mentoring"
    ],

    # ══ Human Resource Management (HRM) ══
    "Recruiter": [
        "Recruitment", "Communication", "Interviewing",
        "Talent Acquisition", "Human Resource Management", "Networking", "Negotiation", "Social Media"
    ],
    "Talent Acquisition Specialist": [
        "Talent Acquisition", "Recruitment", "Communication",
        "Interviewing", "HR Analytics", "Employer Branding", "Social Media", "Negotiation"
    ],
    "Training & Development Manager": [
        "Training & Development", "Instructional Design", "Communication",
        "Leadership", "Learning Management Systems", "Presentation", "Curriculum Development", "Coaching"
    ],
    "Compensation & Benefits Analyst": [
        "Compensation Analysis", "Human Resource Management", "Excel",
        "Data Analysis", "Benefits Administration", "Compliance", "Communication", "HRIS"
    ],
    "HR Business Partner": [
        "Human Resource Management", "Business Strategy", "Communication",
        "Employee Relations", "Performance Management", "Leadership", "Data Analysis", "Change Management"
    ],
    "Organizational Development Specialist": [
        "Organizational Development", "Change Management", "Communication",
        "Leadership", "Training & Development", "Data Analysis", "Coaching", "Strategic Planning"
    ],

    # ══ Mathematics ══
    "Data Analyst": [
        "Data Analysis", "SQL", "Python", "Excel",
        "Statistics", "Data Visualization", "Power BI", "Communication"
    ],
    "Statistician": [
        "Statistics", "R", "Python", "Data Analysis",
        "SPSS", "Probability", "Research Methodology", "Excel"
    ],
    "Actuary": [
        "Statistics", "Probability", "Financial Modeling", "Excel",
        "Risk Assessment", "Data Analysis", "Python", "Communication"
    ],
    "University Lecturer": [
        "Research Methodology", "Technical Writing", "Communication",
        "Presentation", "Curriculum Development", "Statistics", "Mentoring", "Subject Expertise"
    ],
    "Research Scientist": [
        "Research Methodology", "Data Analysis", "Python",
        "Technical Writing", "Statistics", "Problem Solving", "Peer Review", "Grant Writing"
    ],
    "Operations Research Analyst": [
        "Operations Research", "MATLAB", "Python", "Statistics",
        "Linear Programming", "Data Analysis", "Excel", "Problem Solving"
    ],

    # ══ Physics ══
    "Medical Physicist": [
        "Radiation Physics", "MATLAB", "Medical Imaging", "Data Analysis",
        "Radiation Safety", "Python", "Research Methodology", "Quality Control"
    ],
    "Optics Engineer": [
        "Optics", "MATLAB", "Laser Technology", "Signal Processing",
        "Physics Simulation", "Data Analysis", "AutoCAD", "Research Methodology"
    ],
    "Semiconductor Engineer": [
        "Semiconductor Physics", "MATLAB", "Clean Room Techniques",
        "Circuit Design", "VHDL/Verilog", "Material Science", "Data Analysis", "Research Methodology"
    ],

    # ══ Chemistry ══
    "Research Chemist": [
        "Organic Chemistry", "Analytical Chemistry", "Lab Techniques",
        "Data Analysis", "Research Methodology", "Technical Writing", "Quality Control", "Spectroscopy"
    ],
    "Chemical Engineer": [
        "Chemical Processes", "MATLAB", "Process Optimization",
        "Material Science", "Thermodynamics", "AutoCAD", "Safety Management", "Data Analysis"
    ],
    "Quality Control Analyst": [
        "Quality Control", "Lab Techniques", "Analytical Chemistry",
        "ISO Standards", "Documentation", "Data Analysis", "Statistical Process Control", "Communication"
    ],
    "Pharmaceutical Researcher": [
        "Pharmaceutical Science", "Lab Techniques", "Research Methodology",
        "Drug Development", "Analytical Chemistry", "Data Analysis", "Technical Writing", "Quality Control"
    ],
    "Environmental Chemist": [
        "Environmental Chemistry", "Analytical Chemistry", "Lab Techniques",
        "Data Analysis", "Environmental Law", "Research Methodology", "Sampling Techniques", "Technical Writing"
    ],

    # ══ Statistics ══
    "Business Intelligence Analyst": [
        "SQL", "Power BI", "Tableau", "Data Visualization",
        "Excel", "Statistics", "Data Warehousing", "Python"
    ],

    # ══ Biotechnology ══
    "Biotechnologist": [
        "Molecular Biology", "Lab Techniques", "Bioinformatics",
        "Research Methodology", "Data Analysis", "Technical Writing", "Gene Expression", "Quality Control"
    ],
    "Bioinformatician": [
        "Bioinformatics", "Python", "R", "Genomics",
        "Data Analysis", "Statistics", "Machine Learning", "Research Methodology"
    ],
    "Quality Control Scientist": [
        "Quality Control", "Lab Techniques", "ISO Standards",
        "Documentation", "Analytical Chemistry", "Data Analysis", "Statistical Process Control", "GMP"
    ],

    # ══ Environmental Science ══
    "Environmental Consultant": [
        "Environmental Impact Assessment", "Sustainability", "GIS",
        "Data Analysis", "Environmental Law", "Communication", "Technical Writing", "Policy Analysis"
    ],
    "Policy Analyst": [
        "Policy Analysis", "Research Methodology", "Data Analysis",
        "Communication", "Technical Writing", "Statistics", "Critical Thinking", "Presentation"
    ],
    "Government Advisor": [
        "Policy Analysis", "Communication", "Research Methodology",
        "Data Analysis", "Leadership", "Strategic Planning", "Technical Writing", "Public Speaking"
    ],
    "NGO Specialist": [
        "Project Management", "Communication", "Community Engagement",
        "Fundraising", "Data Analysis", "Report Writing", "Sustainability", "Policy Analysis"
    ],

    # ══ English ══
    "Teacher / Lecturer": [
        "Communication", "Curriculum Development", "Presentation",
        "Research Methodology", "Mentoring", "Assessment Design", "Technical Writing", "Pedagogy"
    ],
    "Journalist": [
        "Journalism", "Communication", "Research Methodology",
        "Copywriting", "Critical Thinking", "Media Ethics", "Photography", "Social Media"
    ],
    "Content Writer": [
        "Copywriting", "SEO", "Communication", "Content Marketing",
        "Editing", "Research Methodology", "Social Media", "Creative Writing"
    ],
    "Editor / Publisher": [
        "Editing", "Proofreading", "Communication", "Publishing",
        "Content Management Systems", "Copywriting", "Project Management", "Creative Writing"
    ],
    "Public Relations Specialist": [
        "Communication", "Media Relations", "Copywriting",
        "Social Media", "Crisis Communication", "Event Management", "Public Speaking", "Branding"
    ],
    "Translator": [
        "Translation", "Communication", "Cultural Awareness",
        "Proofreading", "Language Proficiency", "Research Methodology", "Editing", "Localization"
    ],
    "Media Professional": [
        "Media Production", "Communication", "Video Editing",
        "Photography", "Social Media", "Content Marketing", "Creative Thinking", "Journalism"
    ],

    # ══ Bangla ══
    "Author / Writer": [
        "Creative Writing", "Communication", "Research Methodology",
        "Editing", "Proofreading", "Publishing", "Critical Thinking", "Storytelling"
    ],
    "Editor": [
        "Editing", "Proofreading", "Communication",
        "Publishing", "Creative Writing", "Content Management Systems", "Attention to Detail", "Research Methodology"
    ],
    "Cultural Researcher": [
        "Research Methodology", "Communication", "Cultural Awareness",
        "Technical Writing", "Data Analysis", "Critical Thinking", "Presentation", "Fieldwork"
    ],

    # ══ History ══
    "Historian": [
        "Research Methodology", "Technical Writing", "Critical Thinking",
        "Archival Research", "Data Analysis", "Communication", "Presentation", "Historiography"
    ],
    "Museum Curator": [
        "Museum Management", "Research Methodology", "Communication",
        "Archival Research", "Presentation", "Cultural Awareness", "Project Management", "Exhibition Design"
    ],
    "Archivist": [
        "Archival Research", "Documentation", "Research Methodology",
        "Data Management", "Communication", "Cataloguing", "Digital Preservation", "Attention to Detail"
    ],

    # ══ Philosophy ══
    "Ethicist": [
        "Critical Thinking", "Ethics", "Communication",
        "Research Methodology", "Technical Writing", "Problem Solving", "Presentation", "Argumentation"
    ],
    "Writer / Author": [
        "Creative Writing", "Critical Thinking", "Communication",
        "Research Methodology", "Editing", "Publishing", "Argumentation", "Storytelling"
    ],
    "Human Rights Advocate": [
        "Human Rights Law", "Communication", "Research Methodology",
        "Critical Thinking", "Public Speaking", "Policy Analysis", "Community Engagement", "Report Writing"
    ],

    # ══ Economics ══
    "Economist": [
        "Economics", "Data Analysis", "Statistics", "Python",
        "Financial Modeling", "Research Methodology", "Excel", "Communication"
    ],
    "Research Analyst": [
        "Research Methodology", "Data Analysis", "Statistics",
        "Excel", "Communication", "Technical Writing", "Critical Thinking", "Python"
    ],
    "Development Specialist": [
        "Development Economics", "Project Management", "Data Analysis",
        "Communication", "Research Methodology", "Policy Analysis", "Community Engagement", "Report Writing"
    ],
    "Government Economic Advisor": [
        "Economics", "Policy Analysis", "Data Analysis",
        "Communication", "Financial Modeling", "Statistics", "Strategic Planning", "Public Speaking"
    ],

    # ══ Sociology ══
    "Sociologist": [
        "Research Methodology", "Data Analysis", "Statistics",
        "Critical Thinking", "Communication", "Survey Design", "SPSS", "Technical Writing"
    ],
    "Social Worker": [
        "Counseling", "Communication", "Community Engagement",
        "Case Management", "Crisis Intervention", "Empathy", "Problem Solving", "Report Writing"
    ],
    "Community Developer": [
        "Community Engagement", "Communication", "Project Management",
        "Fundraising", "Data Analysis", "Leadership", "Report Writing", "Public Speaking"
    ],

    # ══ Political Science ══
    "Political Analyst": [
        "Political Analysis", "Research Methodology", "Data Analysis",
        "Communication", "Critical Thinking", "Technical Writing", "Public Speaking", "Statistics"
    ],
    "Policy Advisor": [
        "Policy Analysis", "Research Methodology", "Communication",
        "Data Analysis", "Strategic Planning", "Technical Writing", "Public Speaking", "Leadership"
    ],
    "Government Officer": [
        "Public Administration", "Communication", "Policy Analysis",
        "Leadership", "Data Analysis", "Decision Making", "Report Writing", "Compliance"
    ],
    "Diplomat": [
        "Diplomacy", "Communication", "Negotiation",
        "Cultural Awareness", "Public Speaking", "Policy Analysis", "Languages", "International Law"
    ],

    # ══ International Relations ══
    "Foreign Service Officer": [
        "Diplomacy", "Communication", "Negotiation",
        "Languages", "Cultural Awareness", "International Law", "Public Speaking", "Policy Analysis"
    ],
    "International Development Specialist": [
        "Development Economics", "Project Management", "Communication",
        "Research Methodology", "Data Analysis", "Policy Analysis", "Community Engagement", "Grant Writing"
    ],

    # ══ Public Administration ══
    "Public Administrator": [
        "Public Administration", "Policy Analysis", "Communication",
        "Leadership", "Budgeting", "Project Management", "Data Analysis", "Decision Making"
    ],
    "NGO Manager": [
        "Project Management", "Communication", "Fundraising",
        "Leadership", "Community Engagement", "Budgeting", "Report Writing", "Strategic Planning"
    ],
    "Civil Servant": [
        "Public Administration", "Communication", "Policy Analysis",
        "Report Writing", "Data Analysis", "Compliance", "Decision Making", "Leadership"
    ],

    # ══ Pharmacy ══
    "Pharmacist": [
        "Pharmacology", "Pharmaceutical Science", "Patient Counseling",
        "Drug Interactions", "Compliance", "Communication", "Quality Control", "Lab Techniques"
    ],
    "Drug Research Scientist": [
        "Drug Development", "Research Methodology", "Lab Techniques",
        "Data Analysis", "Pharmaceutical Science", "Analytical Chemistry", "Technical Writing", "Quality Control"
    ],
    "Pharmaceutical Industry Manager": [
        "Pharmaceutical Science", "Project Management", "Quality Control",
        "Regulatory Affairs", "Communication", "Leadership", "Supply Chain Management", "GMP"
    ],
    "Clinical Researcher": [
        "Clinical Research", "Research Methodology", "Data Analysis",
        "Statistics", "Technical Writing", "Communication", "Lab Techniques", "Regulatory Affairs"
    ],
    "Regulatory Affairs Specialist": [
        "Regulatory Affairs", "Compliance", "Technical Writing",
        "Communication", "Pharmaceutical Science", "Quality Control", "Documentation", "Policy Analysis"
    ],

    # ══ Public Health ══
    "Public Health Officer": [
        "Public Health", "Epidemiology", "Data Analysis",
        "Communication", "Policy Analysis", "Statistics", "Community Engagement", "Report Writing"
    ],
    "Epidemiologist": [
        "Epidemiology", "Statistics", "Data Analysis", "Python",
        "Research Methodology", "Public Health", "Biostatistics", "Communication"
    ],
    "Health Policy Analyst": [
        "Health Policy", "Policy Analysis", "Data Analysis",
        "Communication", "Research Methodology", "Statistics", "Technical Writing", "Public Health"
    ],
    "NGO Health Specialist": [
        "Public Health", "Community Engagement", "Communication",
        "Project Management", "Data Analysis", "Report Writing", "Fundraising", "Health Education"
    ],
    "Community Health Worker": [
        "Community Engagement", "Communication", "Health Education",
        "Public Health", "Counseling", "Data Collection", "Empathy", "Report Writing"
    ],

    # ══ Nursing ══
    "Registered Nurse": [
        "Patient Care", "Clinical Skills", "Communication",
        "Medical Documentation", "Pharmacology", "Emergency Care", "Teamwork", "Empathy"
    ],
    "Clinical Nurse Specialist": [
        "Clinical Skills", "Patient Care", "Research Methodology",
        "Advanced Nursing", "Communication", "Leadership", "Medical Documentation", "Evidence-Based Practice"
    ],
    "Nurse Educator": [
        "Pedagogy", "Clinical Skills", "Communication",
        "Curriculum Development", "Mentoring", "Research Methodology", "Assessment Design", "Presentation"
    ],
    "Healthcare Administrator": [
        "Healthcare Management", "Budgeting", "Communication",
        "Leadership", "Compliance", "Data Analysis", "Quality Control", "Strategic Planning"
    ],
    "Community Health Nurse": [
        "Community Engagement", "Patient Care", "Communication",
        "Health Education", "Public Health", "Counseling", "Data Collection", "Empathy"
    ],

    # ══ Law (LLB) ══
    "Lawyer / Advocate": [
        "Legal Research", "Communication", "Argumentation",
        "Critical Thinking", "Negotiation", "Legal Writing", "Court Procedures", "Ethics"
    ],
    "Legal Consultant": [
        "Legal Research", "Communication", "Contract Law",
        "Corporate Law", "Negotiation", "Legal Writing", "Compliance", "Problem Solving"
    ],
    "Judge": [
        "Legal Research", "Critical Thinking", "Communication",
        "Decision Making", "Ethics", "Court Procedures", "Argumentation", "Legal Writing"
    ],
    "Corporate Legal Advisor": [
        "Corporate Law", "Contract Law", "Legal Research",
        "Communication", "Compliance", "Negotiation", "Legal Writing", "Risk Assessment"
    ],
    "Public Prosecutor": [
        "Criminal Law", "Legal Research", "Communication",
        "Argumentation", "Court Procedures", "Evidence Analysis", "Legal Writing", "Ethics"
    ],
    "Legal Researcher": [
        "Legal Research", "Technical Writing", "Communication",
        "Critical Thinking", "Data Analysis", "Attention to Detail", "Legal Writing", "Research Methodology"
    ],
    "Human Rights Lawyer": [
        "Human Rights Law", "Legal Research", "Communication",
        "Argumentation", "International Law", "Legal Writing", "Community Engagement", "Ethics"
    ],
}


def run():
    app = create_app()
    with app.app_context():
        careers = CareerPath.query.all()
        career_map = {c.title: c for c in careers}

        total_links = 0
        skipped = 0
        skills_created = 0

        for career_title, skill_names in CAREER_SKILLS.items():
            career = career_map.get(career_title)
            if not career:
                print(f"  ⚠ Career not found in DB: '{career_title}' — skipping")
                continue

            for skill_name in skill_names:
                # Find or create master Skill
                master = Skill.query.filter(
                    db.func.lower(Skill.skill_name) == skill_name.lower()
                ).first()
                if not master:
                    master = Skill(skill_name=skill_name, department=None)
                    db.session.add(master)
                    db.session.flush()
                    skills_created += 1

                # Check if link already exists
                exists = CareerRequiredSkill.query.filter_by(
                    career_id=career.id, skill_id=master.id
                ).first()
                if exists:
                    skipped += 1
                    continue

                link = CareerRequiredSkill(
                    career_id=career.id,
                    skill_id=master.id,
                    importance_level="High"
                )
                db.session.add(link)
                total_links += 1

        db.session.commit()

        # Summary
        mapped_count = len(set(CAREER_SKILLS.keys()) & set(career_map.keys()))
        unmapped = set(career_map.keys()) - set(CAREER_SKILLS.keys())

        print(f"\n{'='*60}")
        print(f"  Career-Skill Seeding Complete")
        print(f"{'='*60}")
        print(f"  Careers mapped:       {mapped_count}")
        print(f"  New skill links:      {total_links}")
        print(f"  Duplicate links:      {skipped}")
        print(f"  New master skills:    {skills_created}")
        if unmapped:
            print(f"\n  Careers WITHOUT mappings ({len(unmapped)}):")
            for name in sorted(unmapped):
                print(f"    • {name}")
        print()

if __name__ == "__main__":
    run()
