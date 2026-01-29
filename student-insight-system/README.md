🎓 Student Academic Insight System
🔹 Purpose (In Short)

This project is a student-focused academic insight system.

It helps:

Students understand academic load, burnout risk, and learning feasibility

Teachers see a student’s true academic strength beyond CGPA

Machine Learning will be used to analyze student records and predict academic risk and burnout.

🔹 Tech Stack

Backend:

Python

Flask

Flask-JWT-Extended (Login & Authentication)

Machine Learning (Scikit-learn – later)

Database (later)

Frontend

HTML (Jinja templates)

CSS (basic styling)

🔹 How the System Works (Simple)

User registers and logs in

System issues a JWT token

User accesses dashboard based on role:

Student → Student Dashboard

Teacher → Teacher Dashboard

Student data will later be analyzed by ML models

🔹 Project Folder Structure (IMPORTANT)
student-insight-system/
│
├── app.py
├── config.py
├── requirements.txt
│
├── auth/              # BACKEND (Authentication logic)
│   └── routes.py
│
├── dashboard/         # BACKEND (Dashboard routes)
│   └── routes.py
│
├── templates/         # FRONTEND (HTML pages)
│   ├── home.html
│   ├── login.html
│   ├── register.html
│   ├── student_dashboard.html
│   └── teacher_dashboard.html
│
├── static/            # FRONTEND (CSS, JS)
│   └── style.css
│
└── ml/                # Machine Learning (future)
    └── model.pkl

🔹 Backend Folders (Flask Logic)

        auth/
Handles:

        Login

        Registration

        JWT token creation

dashboard/
Handles:

    Student dashboard routes

    Teacher dashboard routes

    Role-based access control

app.py
    ain entry point of the Flask app
    Registers all routes and starts the server

🔹 Frontend Folders

templates/
    Contains all HTML pages rendered by Flask

static/
    Contains CSS (and JS later)

🔹 Current Status

✅ Login & Registration
✅ JWT Authentication
✅ Student & Teacher dashboards
⏳ Database integration (next)
⏳ Machine learning integration

🔹 Run the Project
pip install -r requirements.txt
python app.py


Open:

http://127.0.0.1:5000/