# PostgreSQL Setup Guide

## ✅ Installation Complete

Your Flask application is now configured to use PostgreSQL!

---

## 📋 What Was Done

1. ✅ Installed `psycopg2-binary` (PostgreSQL adapter)
2. ✅ Installed `flask-migrate` (database migrations)
3. ✅ Updated `config.py` with PostgreSQL connection string
4. ✅ Enhanced `app.py` with Flask-Migrate and connection testing
5. ✅ Updated `requirements.txt` with new dependencies

---

## 🔧 Next Steps

### **Step 1: Set Your PostgreSQL Password**

Open [`config.py`](file:///D:/Project/student-insight-system/student-insight-system/config.py) and **replace `YOUR_DB_PASSWORD`** with your actual PostgreSQL password:

```python
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:YOUR_ACTUAL_PASSWORD@localhost:5432/student_insight_system'
```

> **Don't remember your password?** You can reset it using pgAdmin or PostgreSQL command line.

---

### **Step 2: Verify PostgreSQL is Running**

Make sure your PostgreSQL service is running:

1. Open **Services** (Windows + R, type `services.msc`)
2. Look for **"postgresql-x64-[version]"**
3. Ensure status is **"Running"**

Or check via command line:
```bash
psql -U postgres -c "SELECT version();"
```

---

### **Step 3: Verify Database Exists**

Confirm that the `student_insight_system` database exists:

```bash
psql -U postgres -c "\l" | findstr student_insight_system
```

If it doesn't exist, create it:
```sql
psql -U postgres
CREATE DATABASE student_insight_system;
\q
```

---

### **Step 4: Test the Connection**

Run your Flask app to test the connection:

```bash
python app.py
```

**Expected Output:**
```
============================================================
✅ Successfully connected to PostgreSQL database!
   Database: student_insight_system
   Host: localhost:5432
============================================================
```

**If Connection Fails**, you'll see troubleshooting tips in the error message.

---

### **Step 5: Initialize Database Migrations**

Set up Flask-Migrate for managing database schema changes:

```bash
# Initialize migrations folder (only run once)
python -m flask db init

# Create initial migration based on your models
python -m flask db migrate -m "Initial migration with comprehensive models"

# Apply the migration to create all tables
python -m flask db upgrade
```

---

## 📊 Database Models

Your database now includes these comprehensive models:

### **Master Data**
- `CourseCatalog` - Official course list
- `Skill` - Normalized skills
- `CareerPath` - Career definitions
- `CareerRequiredSkill` - Career-skill mappings

### **Student Records**
- `StudentProfile` - Student information
- `StudentAcademicRecord` - Course grades & confidence
- `StudentGoal` - Career goals

### **Tracking**
- `StudySession` - Granular study logs
- `WeeklyUpdate` - Weekly snapshots

### **Chat**
- `ChatHistory` - Chat interactions

---

## 🔍 Troubleshooting

### **Error: "password authentication failed"**
- Check your password in `config.py`
- Verify with: `psql -U postgres`

### **Error: "database does not exist"**
- Create it: `psql -U postgres -c "CREATE DATABASE student_insight_system;"`

### **Error: "could not connect to server"**
- Ensure PostgreSQL is running (check Services)
- Verify port 5432 is in use: `netstat -an | findstr 5432`

### **Error: "relation does not exist"**
- Run migrations: `python -m flask db upgrade`

---

## 🔄 Switching Between SQLite and PostgreSQL

If you need to switch back to SQLite for testing, edit `config.py`:

**Comment out PostgreSQL:**
```python
# SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:password@localhost:5432/student_insight_system'
```

**Uncomment SQLite:**
```python
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'student_insight.db')}"
```

---

## 📝 Connection String Format

```
postgresql://username:password@host:port/database_name
          │         │        │    │          │
          │         │        │    │          └─ Database name
          │         │        │    └─ Port (default: 5432)
          │         │        └─ Host (localhost for local)
          │         └─ Your PostgreSQL password
          └─ Username (default: postgres)
```

---

## ✨ Benefits of PostgreSQL

**Over SQLite:**
- ✅ Better for production environments
- ✅ Supports concurrent connections
- ✅ Advanced features (JSON, full-text search)
- ✅ Better performance with large datasets
- ✅ ACID compliance with better integrity

---

## 🚀 Ready to Go!

Once you complete the steps above, your application will be ready to:
- Store student data in PostgreSQL
- Track study sessions
- Generate visualizations
- Chat with the system
