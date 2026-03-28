# Software Requirements Specification (SRS)
## Student Insight System
**Version:** 1.0  
**Date:** 26 March, 2026
**Prepared by:** Antigravity AI
**Institution:** Daffodil International University  
**Tech Stack:** Python, Flask, SQLAlchemy, Flask-Mail, Flask-APScheduler, Flask-JWT-Extended, SQLite/PostgreSQL, HTML/CSS/JS, Chart.js  
**Status:** Draft

---

## 1. Introduction
### 1.1 Purpose
The purpose of this document is to define the software requirements for the **Student Insight System**. It specifies the system's architecture, features, user interfaces, non-functional aspects, and design constraints to guide future development and maintenance.

### 1.2 Project Scope
The Student Insight System is a web-based educational platform designed for students and teachers of Daffodil International University. It enables students to track their academic performance, set and achieve career goals, map their skills, log study sessions, and receive AI-generated insights. For teachers, the system provides a dashboard to monitor assigned students, track their performance KPIs, receive automated alerts regarding at-risk students, and maintain notes.
**What it does NOT do:** 
The system does not manage actual course enrollments or directly interface with the university's primary grading system (ERP) in the current iteration; it relies on self-reported and synced data. It does not handle tuition fee payments or university administration tasks.

### 1.3 Definitions, Acronyms & Abbreviations
- **SRS**: Software Requirements Specification
- **JWT**: JSON Web Token
- **CGPA**: Cumulative Grade Point Average
- **AI**: Artificial Intelligence
- **API**: Application Programming Interface
- **KPI**: Key Performance Indicator

### 1.4 References
- Flask Framework Documentation
- SQLAlchemy ORM Documentation
- Chart.js Documentation
- Gemini AI API Documentation
- Project Source Code & Route Architectures

### 1.5 Document Overview
This document is organized into Sections 1 through 8. Section 2 provides a general overview of the product, user classes, and operating environment. Section 3 details the functional requirements of each system feature. Section 4 describes external interfaces. Section 5 specifies non-functional requirements. Sections 6, 7, and 8 cover data models, constraints, and appendices respectively.

---

## 2. Overall Description
### 2.1 Product Perspective
The Student Insight System operates as a standalone web application designed for the DIU academic environment. It utilizes a monolithic architecture with a Python/Flask backend and a traditional server-rendered template frontend, optionally enhanced with JavaScript for dynamic features. It integrates with Google Gemini AI for generating intelligent reports and action plans.

### 2.2 Product Functions
- User Registration and Secure JWT Authentication
- Student and Teacher Profile Management
- Student Analytics Dashboard (CGPA trend, attendance, assessments)
- AI Insight Reports and Skill Action Plans
- Study Session and Weekly Routine Tracking
- Teacher Dashboard with Key Performance Indicators
- Automated Alerts for At-Risk Students
- Teacher-Student Note System
- CV/Resume Generation from Profile Data

### 2.3 User Classes and Characteristics
#### 2.3.1 Student
- **Responsibilities**: Keep profile updated, log study sessions, track skills and goals, submit weekly check-ins, view insights.
- **Access Level**: Restricted to their own profile, academic data, and dashboards. 
- **Technical Skill**: Basic web browsing proficiency.

#### 2.3.2 Teacher
- **Responsibilities**: Monitor academic progress of assigned students, review system-generated alerts, add anecdotal notes, track class performance trends.
- **Access Level**: Authorized to view details of assigned students (mapped via `TeacherAssignment`). Cannot alter a student's core demographic data but can add notes and resolve alerts.
- **Technical Skill**: Basic web browsing proficiency.

### 2.4 Operating Environment
- **Server-side**: Python 3.x, Flask web framework.
- **Client-side**: Modern standard web browsers (Chrome, Firefox, Safari, Edge) with JavaScript enabled.
- **Database**: PostgreSQL (production) or SQLite (development/testing) managed via SQLAlchemy ORM.
- **Deployment**: Configurable via environment variables.

### 2.5 Design and Implementation Constraints
- **Framework Constraints**: Built entirely on the Flask ecosystem, relying on Flask blueprints, Flask-JWT-Extended, and Flask-SQLAlchemy.
- **AI Constraints**: Relies on external Gemini AI API; availability and accuracy depend on the external service.
- **Database Constraints**: Designed for relational mechanics. SQLite is supported for testing but PostgreSQL must be used in production.

### 2.6 Assumptions and Dependencies
- Users have reliable internet access.
- Third-party API (Gemini AI) remains available and backwards-compatible.
- Appropriate Python packages listed in `requirements.txt` are installed.

---

## 3. System Features & Functional Requirements

### 3.1 User Authentication
**3.1.1 Description** — Handles user registration, secure login, and session management using JSON Web Tokens (JWT) stored in HttpOnly cookies.
**3.1.2 User Interaction Flow** — User submits email, password, and role to `/register` or `/login`. The backend validates the input and sets a JWT cookie upon success, redirecting them to their respective dashboard.
**3.1.3 Functional Requirements:**  
- FR-01: The system SHALL allow users to register as either a Student or Teacher.
- FR-02: The system SHALL authenticate users using an email and password via JWT cookies.
- FR-03: The system SHALL redirect authenticated students to `/student/dashboard` and teachers to `/teacher/dashboard`.
- FR-04: The system SHALL explicitly clear JWT cookies and cache headers when a user logs out.

### 3.2 Student Profile & Onboarding
**3.2.1 Description** — Manages student demographic, academic, and professional goal data. Includes an onboarding flow for new users.
**3.2.2 User Interaction Flow** — New students are routed to an onboarding checklist. Students can navigate to Settings/Profile to update CGPA, department, university, and career goals.
**3.2.3 Functional Requirements:**  
- FR-05: The system SHALL redirect newly registered students to the onboarding workflow before granting full dashboard access.
- FR-06: The system SHALL allow students to upload an optional profile picture.
- FR-07: The system SHALL allow students to update their target CGPA and career goals.
- FR-08: The system SHALL allow students to configure email notification preferences (weekly report, new assignments).

### 3.3 Student Dashboard & Analytics
**3.3.1 Description** — The main landing page for students displaying their academic performance trends, attendance, and current task statuses.
**3.3.2 User Interaction Flow** — The student visits `/student/dashboard`. The system fetches their academic metrics and renders charts and summary cards.
**3.3.3 Functional Requirements:**  
- FR-09: The system SHALL retrieve and display a list of the student's courses and respective grades.
- FR-10: The system SHALL display the student's CGPA based on uploaded academic records.
- FR-11: The system SHALL track and display the student's assessment and assignment statuses.
- FR-12: The system SHALL graphically plot the student's performance trend across semesters using Chart.js.

### 3.4 Skill & Career Tracking
**3.4.1 Description** — Students can add technical and soft skills, rate their proficiency, and align them with a mapped career path (e.g., Software Engineering).
**3.4.2 User Interaction Flow** — Student selects skills. The system evaluates them against department-defined career paths and generates recommended "Action Plans" using AI.
**3.4.3 Functional Requirements:**  
- FR-13: The system SHALL store student-defined skills and corresponding proficiency scores (0-100).
- FR-14: The system SHALL provide an API to generate an AI-driven action plan for a specific skill.
- FR-15: The system SHALL increase a skill's proficiency score when its associated action plan is marked as complete.
- FR-16: The system SHALL map the student's primary career goal against a pre-defined matrix of relevant department careers.

### 3.5 AI Insight Generation
**3.5.1 Description** — Generates a personalized text report analyzing the student's current trajectory, risks, and recommendations using Gemini AI.
**3.5.2 User Interaction Flow** — Student clicks "Generate Insight" and fills out a form. Backend aggregates DB metrics and sends a prompt to Gemini AI. The returned HTML report is displayed.
**3.5.3 Functional Requirements:**  
- FR-17: The system SHALL aggregate the student's CGPA, skill risk scores, and weekly checklist data to form an AI context block.
- FR-18: The system SHALL successfully call the Gemini AI service and parse the response into a structured HTML report.
- FR-19: The system SHALL save the generated AI insight report to the database for future reference.
- FR-20: The system SHALL display the generated insight report visually on the student's dashboard.

### 3.6 Study Sessions & Weekly Routine
**3.6.1 Description** — Students can manually log hours studied per subject and submit a weekly reflection to track burnout and consistency.
**3.6.2 User Interaction Flow** — Student adds a session specifying course and duration. Weekly, they submit a slider-based reflection regarding stress/burnout.
**3.6.3 Functional Requirements:**  
- FR-21: The system SHALL allow students to log study session durations against specific enrolled courses.
- FR-22: The system SHALL allow students to submit a weekly reflection capturing perceived burnout risk and goal achievability.
- FR-23: The system SHALL calculate the rolling average of study hours over a 4-week period. [PARTIAL]
- FR-24: The system SHALL determine an algorithmic "status label" based on the student's weekly input.

### 3.7 Teacher Dashboard & Student Monitoring
**3.7.1 Description** — Provides teachers with a real-time overview of the students specifically assigned to them, grouped by performance risk.
**3.7.2 User Interaction Flow** — Teacher logs in, views the aggregate KPIs (Total, Good, Average, At Risk), and selects specific students to view detailed analytics.
**3.7.3 Functional Requirements:**  
- FR-25: The system SHALL display aggregate KPI counts of assigned students grouped by performance status.
- FR-26: The system SHALL enforce access controls such that a teacher may only view data for students mapped to them via `TeacherAssignment`.
- FR-27: The system SHALL provide a filterable list of assigned students containing their name, ID, CGPA, and status.
- FR-28: The system SHALL expose an API to assign or unassign a student to/from a teacher's roster.

### 3.8 Teacher Alerts System
**3.8.1 Description** — Automated flags generated for at-risk behaviors (e.g., dropping CGPA, missing assignments) which the teacher must review and resolve.
**3.8.2 User Interaction Flow** — Alerts appear on the teacher dashboard. The teacher reviews the alert context and clicks "Resolve" to clear it.
**3.8.3 Functional Requirements:**  
- FR-29: The system SHALL aggregate and display unresolved `StudentAlert` entities assigned to the teacher's students.
- FR-30: The system SHALL support sequential pagination for viewing alert history.
- FR-31: The system SHALL allow teachers to mark an individual alert as resolved via a POST request.
- FR-32: The system SHALL provide a batch-resolution capability to mark multiple alerts as resolved simultaneously.

### 3.9 Teacher Notes System
**3.9.1 Description** — A logging feature for teachers to record qualitative observations or interactions regarding a student.
**3.9.2 User Interaction Flow** — On a student's detail page, the teacher submits a text note. The note is appended to the student's timeline.
**3.9.3 Functional Requirements:**  
- FR-33: The system SHALL allow teachers to create and save text-based notes associated with a specific student.
- FR-34: The system SHALL store notes with a timestamp and the authoring teacher's ID.
- FR-35: The system SHALL allow teachers to view a chronological history of all notes they have authored.
- FR-36: The system SHALL NOT allow students to view notes marked as private by the teacher. [PLANNED]

---

## 4. External Interface Requirements
### 4.1 User Interfaces
- **Student Dashboards**: Multi-card layout featuring line graphs for CGPA and interactive onboarding elements.
- **Teacher Dashboards**: Features aggregate KPIs, unread alerts feeds, and a list of assigned students.
- **Student Detail Profile (`student_detail.html`)**: Deep-dive component visible to teachers containing 6 snapshot views (Profile, Academic, Skill, Weekly, Career, AI Insight).
- **Authentication Routes**: Clean, responsive form modals for login, registration, and initial account hookup.

### 4.2 Hardware Interfaces
- No specialized device requirements. The application operates over standard TCP/IP networking targeting conventional operating systems.

### 4.3 Software Interfaces
- **Flask Ecosystem**: Core HTTP routing, database abstractions (SQLAlchemy), and authentication token logic.
- **Chart.js**: Frontend component for plotting statistics dynamically in HTML.

### 4.4 Communication Interfaces
- **HTTP/HTTPS**: Standard web interaction protocol separating the client browser and Flask backend.
- **Gemini AI API**: Encrypted, outbound HTTPS payload dispatch to Google Cloud for Text generation logic.

---

## 5. Non-Functional Requirements
### 5.1 Performance
- Dashboard pages SHALL populate initial template HTML and core database metrics within 2.0 seconds under standard server load configurations.
- API interactions dependent on Gemini AI SHALL timeout and present a friendly user failure message if resolution takes longer than 15 seconds.

### 5.2 Security
- The system SHALL secure all protected routes utilizing JWT tokens. These cookies MUST explicitly skip browser reading via `HttpOnly=True`.
- In standard Production environments (`ProductionConfig`), JWT cookies SHALL enforce HTTPS-only transfers (`Secure=True`).
- Raw textual inputs SHALL be aggressively parameterized by the ORM before committing to prevent SQL Injection attempts.
- Passwords MUST be heavily hashed using modern standard PBKDF2 configurations native to Werkzeug.

### 5.3 Reliability & Availability
- Service logic handling Gemini interactions SHALL catch exceptions caused by external outages or missing tokens to ensure the site thread doesn't crash completely.

### 5.4 Scalability
- Relational mapping between frequently scanned columns (e.g. `teacher_id` > `TeacherAssignment` > `student_id`) SHALL natively leverage B-Tree database indices.

### 5.5 Maintainability
- The framework SHALL preserve MVC logic separation, placing core algorithm/processing logic inside `services/` isolating it away from Flask Route layers.

### 5.6 Portability
- End-user layouts SHALL respond appropriately across Desktop Web and Mobile platforms via standard CSS utility techniques.

### 5.7 Usability
- KPI Dashboards SHALL heavily emphasize visual differentiation mapping to specific alert criteria (e.g., standard Warning color bands across "At-Risk" vs "Good").

---

## 6. Data Requirements
### 6.1 Data Models
The system maps functional behavior onto the following relational clusters:

- **Identity Layer**: 
  - `User`: Base identity (email, password_hash, role).
  - `UserToken`: Revoked/Logout verification layer.
- **Demographic Profiles**: 
  - `StudentProfile`: Linked to User. Captures department, cgpa, section, class_level.
  - `TeacherProfile`: Linked to User. Captures designation, department.
  - `TeacherAssignment`: Core junction table allowing assigned views.
- **Academic Ledgers**:
  - `CourseCatalog`: Master repository of university curriculum elements.
  - `StudentAcademicRecord`: Permanent historical records tied to individual Student instances.
  - `StudentCourse`: Active semester rosters mapping.
- **Progression Modules**:
  - `Skill`, `StudentSkill`: Tracks unique competencies.
  - `ActionPlan`: Tracks steps to remediate deficiencies or push advancement.
  - `CareerPath`, `CareerInterest`, `StudentGoal`: Maps distinct interests into the master framework.
- **Telemetry & Feedback**:
  - `WeeklyUpdate`: Short form time/burnout logging.
  - `StudentInsight`, `AnalyticsResult`: Database caches mapped over raw LLM outputs.
  - `StudentAlert`, `StudentNote`: Distinct manual entries generated via the backend metrics engines.

### 6.2 Data Privacy & Retention
- **Password Storage**: Cryptographic storage mandatory. Explicitly forbids plaintext storage.
- **Tenant Scope Isolation**: Queries querying personal data objects strictly restrict lookups against the explicitly assigned identity ID from the active cookie context.

---

## 7. System Constraints & Limitations
- **Always Online Restriction**: The application lacks PWA integration or offline cache. An active HTTP connection is mandatory.
- **Vendor Lock-in Limitation**: Currently, robust predictive generation relies on an active session against Gemini. Dropping this dependency fundamentally neuters "Action Plans" and "Insight Engine" outputs.
- **Hard Invalidations**: JWT cookies enforce rigid timeouts without seamless background rotation in development logic.

---

## 8. Appendix
### 8.1 Use Case Summary
**Student Target Persona**: Registers an account > Completes Onboarding checklist > Submits weekly routines > Triggers AI Action plans for skill adjustments > Tracks generated feedback visually.

**Teacher Target Persona**: Logs onto portal > Scans KPI status matrix > Evaluates highest-risk triggers matching their assigned cohort block > Resolves alerts > Modulates individual records via the Note Engine.

### 8.2 Database ER Description
The internal object model anchors via a single table inheritance configuration at `User`. `StudentProfile` & `TeacherProfile` branch via a 1:1 mapping. Volatile dynamic telemetry (`Alerts`, `Notes`, `ActionPlans`, `Insights`) clusters around a traditional Many:1 root back to the active `StudentProfile`. To enforce access, isolated subsets are resolved exclusively through `TeacherAssignment`.

### 8.3 Glossary
- **Action Plan**: Systemic checklist mapped from LLM predictions directing a Student on distinct technical growth phases.
- **Insight Report**: Large language parsed heuristic explaining broad scale observations.

### 8.4 Open Issues / Future Enhancements
- Integration of a universal administrative UI panel preventing manual DBA interactions to inject basic master lookup rows (`CourseCatalog`, `Skills`).
- Activation of explicit HTTP dispatch loops to trigger unread warnings via asynchronous notification pipelines.

---

## 9. Discovered vs Expected Features

### 9.1 Discovered in Codebase
- Intricate role-based bifurcation of routing logic dividing Students / Teachers appropriately.
- Robust ORM coverage managing dozens of bespoke features (Academics, Sub-skills, Telemetry, and Notes).
- Pre-built LLM service logic mapped explicitly to Google `GeminiService` injection configurations.
- Detailed implementation of Teacher-centric views supporting paginated alert responses and class-wide performance visualizers.

### 9.2 Expected but Missing/Partial
- **Top Level Administrative Interface**: An app this wide traditionally hosts an `/admin` namespace allowing configuration of master models (Courses, Departments). This is completely absent, relying on raw programmatic DB seed sequences.
- **Explicit Notification Handlers**: References exist anticipating email dispatches, yet core routes skip explicitly executing SMTP logic directly. Configs suggest this delegates externally or is incomplete.
- **Submission Upload Ecosystems**: While grades/assignments exist logically in the graph, complex file handling mechanisms for "Turning In Tasks" directly typically native to standard LMS networks are omitted. 
