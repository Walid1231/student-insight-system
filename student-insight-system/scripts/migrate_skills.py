import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'student_insight.db')

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Starting migration...")

    # 1. Add columns to student_skill table
    try:
        cursor.execute("ALTER TABLE student_skill ADD COLUMN proficiency_score INTEGER DEFAULT 0")
        print("Added proficiency_score to student_skill")
    except sqlite3.OperationalError as e:
        print(f"Skipping Add Column (proficiency_score): {e}")

    try:
        cursor.execute("ALTER TABLE student_skill ADD COLUMN risk_score FLOAT DEFAULT 0.0")
        print("Added risk_score to student_skill")
    except sqlite3.OperationalError as e:
        print(f"Skipping Add Column (risk_score): {e}")

    try:
        cursor.execute("ALTER TABLE student_skill ADD COLUMN last_updated TIMESTAMP")
        print("Added last_updated to student_skill")
    except sqlite3.OperationalError as e:
        print(f"Skipping Add Column (last_updated): {e}")

    # 2. Create student_skill_progress table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_skill_progress (
        id INTEGER PRIMARY KEY,
        student_skill_id INTEGER NOT NULL,
        date DATE,
        proficiency_score INTEGER,
        risk_score FLOAT,
        FOREIGN KEY(student_skill_id) REFERENCES student_skill(id)
    )
    """)
    print("Created table student_skill_progress")

    # 3. Create action_plan table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS action_plan (
        id INTEGER PRIMARY KEY,
        student_id INTEGER NOT NULL,
        skill_id INTEGER,
        title VARCHAR(200) NOT NULL,
        description TEXT,
        status VARCHAR(20) DEFAULT 'pending',
        due_date DATE,
        created_at TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY(student_id) REFERENCES student_profile(id),
        FOREIGN KEY(skill_id) REFERENCES student_skill(id)
    )
    """)
    print("Created table action_plan")

    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
