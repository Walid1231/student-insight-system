# Teacher-Side Feature Proposals

## Current System Audit

Before recommending additions, here's what the teacher-side **currently has**:

### Existing Pages (5)

| # | Page | Route | What It Does |
|---|---|---|---|
| 1 | **Dashboard** | `/teacher/dashboard` | Overview KPI cards (total students, good/avg/at-risk counts), recent alerts list |
| 2 | **My Students** | `/teacher/students` | Paginated list of assigned students with CGPA, department, status pills; assign/unassign functionality |
| 3 | **Alerts** | `/teacher/alerts` | Paginated list of unresolved student alerts (burnout risk, CGPA drop, etc.) with infinite scroll |
| 4 | **Student Detail** | `/teacher/student/<id>` | Deep-dive into one student: CGPA ring, KPI row, analytics charts (CGPA trend, skill radar, burnout gauge, goal probability), teacher notes |
| 5 | **My Notes** | `/teacher/notes` | History of all notes the teacher has written across all students |
| 6 | **Profile** | `/teacher/profile` | Teacher profile (name, department, designation, contact info, picture) |

### Existing APIs (9)

| API | Method | Purpose |
|---|---|---|
| `/api/teacher/unassigned-students` | GET | List students not yet assigned to this teacher |
| `/api/teacher/assign-student` | POST | Assign a student to this teacher |
| `/api/teacher/unassign-student` | DELETE | Remove a student assignment |
| `/api/teacher/alerts/resolve` | POST | Mark an alert as resolved |
| `/api/teacher/alerts/summary` | GET | Breakdown of alerts by severity |
| `/api/teacher/class-skills` | GET | Skill proficiency data for all assigned students |
| `/api/teacher/notes` | GET | Fetch all teacher's notes |
| `/api/teacher/notes` | POST | Create a new note for a student |
| `/api/teacher/profile` | POST | Update teacher profile fields |
| `/api/teacher/profile/picture` | POST | Upload teacher profile picture |

### Existing Data Models (Available for Queries)

The following student data is already in the database and queryable:

- `StudentProfile` — full_name, department, CGPA, career_goal, class_level, section
- `StudentAcademicRecord` — grade_point, semester, course linkage
- `CourseCatalog` — course names, types (Core/GED/Elective), credits
- `StudentSkill` — skill_name, proficiency_score, risk_score
- `StudentGoal` — goal descriptions with achievability probabilities
- `WeeklyUpdate` — hours studied, stress level, mood, sleep, goals achieved
- `StudySession` — per-skill study hours with timestamps
- `Attendance` — present/absent/late records
- `CareerPath` + `CareerRequiredSkill` — career-skill mapping
- `StudentInsight` — AI-generated insights
- `ChatHistory` — AI chat transcripts

---

## What's Missing: Gap Analysis

| Gap | Impact | Why It Matters |
|---|---|---|
| No class-wide analytics view | 🔴 High | Teachers can only look at one student at a time — no way to compare, spot trends, or get a bird's-eye view of the class |
| No AI-generated class report | 🔴 High | AI insights exist for individual students but there's no aggregated AI summary for the teacher |
| No way to message/communicate with students | 🟡 Medium | Notes are private to the teacher — students never see them |
| No scheduling/office hours system | 🟡 Medium | No way for teachers to set availability or students to book time |
| No assignment/assessment management | 🟡 Medium | Assignment/Assessment models exist but there's no teacher UI to create or grade them |
| No export/download capability | 🟢 Low | No way to export student data, reports, or analytics to PDF/CSV |
| No dark mode toggle on teacher side | 🟢 Low | Student side has dark mode but teacher side doesn't have a toggle |
| Dashboard is static KPIs only | 🟡 Medium | No interactive charts, no trend lines, no filters on the main dashboard |

---

## Proposed Features (12)

### 🔴 Tier 1 — High Priority (Core Value Additions)

---

#### Feature 1: Class Analytics Dashboard

> **Problem:** Teachers can only view one student at a time. There's no way to compare performance, spot class-wide trends, or identify which students need immediate attention.

**Page:** `/teacher/analytics`

**UI Concept:**
- **Class CGPA Distribution Chart** — Histogram showing how many students fall in each CGPA range (0-1, 1-2, 2-3, 3-4)
- **Performance Heatmap** — Grid of students × metrics (CGPA, attendance, burnout risk, study hours) with color-coded cells
- **Trend Sparklines** — Small inline charts next to each student showing CGPA direction (↑/↓/→)
- **Department Breakdown** — Donut chart of students by department
- **At-Risk Leaderboard** — Ranked list of students most needing intervention, sorted by a composite risk score
- **Filters** — Filter by department, class level, section, performance status

**Backend Requirements:**
- Aggregate queries across `StudentProfile`, `WeeklyUpdate`, `StudentAcademicRecord`
- Composite risk score calculation: `burnout_risk * 0.3 + (4.0 - cgpa) * 0.4 + absence_rate * 0.3`

**Complexity:** 🟡 Medium (mostly query aggregation + Chart.js frontend)

---

#### Feature 2: AI Class Summary Report

> **Problem:** The system generates AI insights for individual students, but the teacher has no AI-powered summary of the whole class.

**Page:** Button on `/teacher/dashboard` → generates report inline or new page `/teacher/ai-report`

**UI Concept:**
- "Generate Class Report" button with a loading animation
- Report sections:
  - **Executive Summary** — 3-4 sentences about overall class health
  - **Top Concerns** — Students requiring immediate attention and why
  - **Positive Highlights** — Students showing improvement
  - **Skill Gaps** — Common weak areas across the class
  - **Recommendations** — Actionable suggestions for the teacher
- Option to regenerate with different focus (academic, behavioral, career readiness)
- Report history with timestamps

**Backend Requirements:**
- New API: `POST /api/teacher/ai-report` — aggregates student data, calls Gemini API with structured prompt
- Store generated reports in a new `TeacherReport` model for history

**Complexity:** 🟡 Medium (Gemini API integration already exists for student insights)

---

#### Feature 3: Student Communication System (Teacher → Student Messages)

> **Problem:** Teacher notes are private. There's no way for a teacher to send feedback, encouragement, or actionable suggestions directly to a student.

**Page:** Embedded in Student Detail page + new `/student/notifications` feed

**UI Concept:**
- **On Student Detail page:** New "Send Feedback" button alongside existing notes
  - Dropdown: Message type — `Encouragement`, `Academic Concern`, `Action Required`, `General`
  - Textarea with rich formatting
  - Toggle: **Private Note** vs **Send to Student**
- **On Student side:** New notification bell icon showing unread messages from teacher
  - Notifications page listing messages with teacher name, date, type badge
  - Mark as read functionality

**Backend Requirements:**
- Extend `StudentNote` model with `is_visible_to_student` boolean field
- New API: `GET /api/student/teacher-messages` — fetch messages visible to the student
- WebSocket or polling for real-time notification count

**Complexity:** 🟢 Low (extends existing notes system)

---

#### Feature 4: Comparative Student View

> **Problem:** When advising a student, teachers need context — how does this student compare to class averages?

**Page:** Enhanced section on `/teacher/student/<id>`

**UI Concept:**
- **Comparison Panel** below profile hero:
  - CGPA vs Class Average (horizontal bar comparison)
  - Study Hours vs Class Average
  - Attendance vs Class Average
  - Burnout Risk vs Class Average
- **Percentile Rank** — "This student is in the top 30% of your class"
- **Peer Group Comparison** — Compare against students in the same department

**Backend Requirements:**
- Calculate class averages from assigned students
- Percentile ranking query

**Complexity:** 🟢 Low (aggregation queries, frontend display)

---

### 🟡 Tier 2 — Medium Priority (Enhanced Functionality)

---

#### Feature 5: Assignment & Assessment Management

> **Problem:** The database has `Assignment`, `AssignmentSubmission`, `Assessment`, and `AssessmentResult` models but there is **no teacher UI** to create, distribute, or grade them.

**Page:** `/teacher/assignments` + `/teacher/assessments`

**UI Concept:**
- **Create Assignment** form: title, description, due date, course, assigned students (multi-select or class-wide)
- **Submissions Inbox:** List of submitted assignments with status (submitted/late/missing) and grade input
- **Assessment Creator:** Create quizzes with auto-grade capability
- **Gradebook View:** Spreadsheet-style grid of students × assignments with grades

**Backend Requirements:**
- CRUD APIs for assignments and assessments
- Bulk assign to all students in a class/section
- Grade submission API with computed GPA impact

**Complexity:** 🔴 High (full CRUD + new UI pages)

---

#### Feature 6: Attendance Management

> **Problem:** The `Attendance` model exists but there's no teacher interface to record or view attendance.

**Page:** `/teacher/attendance`

**UI Concept:**
- **Quick Roll Call:** Date picker + student list with Present/Absent/Late radio buttons
- **Attendance Overview:** Calendar heatmap showing class-wide attendance patterns
- **Individual Trends:** Attendance sparkline per student
- **Auto-Alert Trigger:** If attendance drops below threshold, auto-generate a `StudentAlert`

**Backend Requirements:**
- CRUD API for `Attendance` records
- Aggregate queries for patterns
- Hook into alert generation pipeline

**Complexity:** 🟡 Medium

---

#### Feature 7: Office Hours / Scheduling System

> **Problem:** No way for teachers to set availability or for students to request meetings.

**Page:** `/teacher/schedule`

**UI Concept:**
- **Availability Calendar:** Weekly view where teacher can mark available time slots
- **Booking Requests:** List of student meeting requests with accept/decline
- **Upcoming Meetings:** Today's and this week's confirmed meetings
- **Student Side:** On student dashboard, "Book Meeting with Advisor" button showing available slots

**Backend Requirements:**
- New models: `AvailabilitySlot`, `MeetingRequest`
- API for CRUD on slots and requests
- Student-facing API for viewing available slots and submitting requests

**Complexity:** 🟡 Medium (new models + 2 new pages, one for each side)

---

#### Feature 8: Student Progress Timeline

> **Problem:** The student detail page shows a snapshot, not a story. Teachers can't see how a student has evolved over time.

**Page:** New tab/section on `/teacher/student/<id>`

**UI Concept:**
- **Vertical Timeline** with event cards:
  - 📊 CGPA change events (e.g., "CGPA dropped from 3.4 to 3.1")
  - 🎯 Goal updates (e.g., "Set career goal: Data Scientist")
  - ⚠️ Alerts triggered
  - 📝 Teacher notes added
  - ✅ Weekly check-ins submitted
  - 🏆 Skill milestones reached
- **Filter by event type**
- **Date range selector**

**Backend Requirements:**
- Combine data from multiple tables with timestamps
- API that returns a unified, sorted event stream

**Complexity:** 🟡 Medium (multi-table join, sorted event feed)

---

### 🟢 Tier 3 — Low Priority (Nice-to-Have Enhancements)

---

#### Feature 9: Export & Reporting

> **Problem:** No way to export data for offline review, parent meetings, or institutional reporting.

**Functionality:**
- **Export Student Report as PDF** — One-click button on student detail page
- **Export Class Roster as CSV** — Download student list with CGPA, department, status
- **Print-Optimized View** — CSS print styles for student detail page

**Backend Requirements:**
- PDF generation library (e.g., `WeasyPrint` or `ReportLab`)
- CSV generation endpoint

**Complexity:** 🟢 Low

---

#### Feature 10: Customizable Dashboard Widgets

> **Problem:** The current dashboard shows fixed KPI cards. Different teachers may want to see different metrics front-and-center.

**UI Concept:**
- Drag-and-drop widget grid (like a modern admin panel)
- Widget options: CGPA distribution, alerts feed, recent notes, attendance summary, study hours chart, at-risk list
- Save layout preference per teacher (stored in `TeacherProfile` or `TeacherSettings`)

**Complexity:** 🔴 High (drag-and-drop UI logic + persistence)

---

#### Feature 11: Batch Actions on Students

> **Problem:** Repetitive actions — sending notes to multiple students, resolving multiple alerts, assigning tags.

**Functionality:**
- Multi-select checkboxes on student list
- Batch actions: "Send note to selected", "Export selected", "Assign tag"
- Select all / deselect all

**Complexity:** 🟢 Low (frontend multi-select with batch API)

---

#### Feature 12: Teacher-to-Teacher Collaboration

> **Problem:** If multiple teachers advise the same student (e.g., homeroom + subject teacher), they can't see each other's notes.

**Functionality:**
- Shared notes visibility toggle: "Share with other advisors of this student"
- "Other Advisors" section on student detail showing which other teachers are also assigned
- Read-only view of shared notes from other teachers

**Backend Requirements:**
- Extend `StudentNote` with `shared_with_teachers` boolean
- Query notes from other teachers for the same student

**Complexity:** 🟢 Low

---

## Recommended Implementation Order

If you want to maximize impact with minimum effort, here's the order I'd suggest:

```
Phase 1 (Quick Wins)
├── Feature 3:  Student Communication (extends existing notes)
├── Feature 4:  Comparative Student View (adds context to existing page)
└── Feature 9:  Export & Reporting (PDF/CSV download)

Phase 2 (Core Enhancements)
├── Feature 1:  Class Analytics Dashboard ⭐ (biggest visual impact)
├── Feature 2:  AI Class Summary Report
└── Feature 8:  Student Progress Timeline

Phase 3 (Full Feature Parity)
├── Feature 6:  Attendance Management
├── Feature 5:  Assignment & Assessment Management
└── Feature 7:  Office Hours / Scheduling

Phase 4 (Polish)
├── Feature 11: Batch Actions
├── Feature 10: Customizable Dashboard
└── Feature 12: Teacher Collaboration
```

---

## Architecture Notes

- All new pages should use the existing `teacher_sidebar.html` component for navigation consistency
- All new APIs should follow the existing pattern: `@teacher_bp.route(...)` + `@jwt_required()` + `_get_teacher_or_403()` guard
- Dark mode support should be included from the start using the existing CSS variable system
- Charts should use Chart.js (already loaded on student detail page)
- AI features should use the existing Gemini API integration pattern from `ml/analytics_engine.py`
