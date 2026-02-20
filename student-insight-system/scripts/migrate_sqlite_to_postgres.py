import sqlite3
import psycopg2
import os
import json
from config import Config
from datetime import datetime

def migrate_data():
    # SQLite Path
    base_dir = os.path.abspath(os.path.dirname(__file__))
    sqlite_path = os.path.join(base_dir, 'instance', 'student_insight.db')
    
    if not os.path.exists(sqlite_path):
        print(f"SQLite DB not found at {sqlite_path}")
        return

    print(f"Migrating data from: {sqlite_path}")
    print(f"To PostgreSQL: {Config.SQLALCHEMY_DATABASE_URI}")

    # Connect to SQLite
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sq_cursor = sqlite_conn.cursor()

    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI)
    pg_cursor = pg_conn.cursor()

    try:
        # 1. Migrate Users
        print("\nMigrating Users...")
        sq_cursor.execute("SELECT * FROM user")
        users = sq_cursor.fetchall()
        for row in users:
            pg_cursor.execute(
                "INSERT INTO \"user\" (id, email, password_hash, role) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                (row['id'], row['email'], row['password_hash'], row['role'])
            )
        print(f"Migrated {len(users)} users.")

        # 2. Migrate Student Profiles
        print("\nMigrating Student Profiles...")
        sq_cursor.execute("SELECT * FROM student_profile")
        profiles = sq_cursor.fetchall()
        for row in profiles:
            # Handle potentially missing columns in old sqlite if schema changed, but assuming equality for now
            pg_cursor.execute(
                """INSERT INTO student_profile 
                   (id, user_id, full_name, department, class_level, section, current_cgpa, last_activity, 
                    grading_scale, current_semester, expected_graduation_date, completed_credits) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                   ON CONFLICT (id) DO NOTHING""",
                (row['id'], row['user_id'], row['full_name'], row['department'], row['class_level'], 
                 row['section'], row['current_cgpa'], row['last_activity'], 
                 row['grading_scale'] if 'grading_scale' in row.keys() else 4.0,
                 row['current_semester'] if 'current_semester' in row.keys() else 1,
                 row['expected_graduation_date'] if 'expected_graduation_date' in row.keys() else None,
                 row['completed_credits'] if 'completed_credits' in row.keys() else 0)
            )
        print(f"Migrated {len(profiles)} student profiles.")
        
        # 2b. Migrate Teacher Profiles
        print("\nMigrating Teacher Profiles...")
        sq_cursor.execute("SELECT * FROM teacher_profile")
        teachers = sq_cursor.fetchall()
        for row in teachers:
            pg_cursor.execute(
                """INSERT INTO teacher_profile (id, user_id, full_name, department, subject_specialization)
                   VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING""",
                (row['id'], row['user_id'], row['full_name'], row['department'], row['subject_specialization'])
            )
            
        # 3. Migrate Related Tables (Order matters for foreign keys)
        
        tables_to_migrate = [
            'course_catalog', 'skills', 'career_paths', # Master data first
            'career_required_skills',
            'attendance', 
            'student_skill', 
            'student_skill_progress', 
            'study_sessions', 
            'weekly_updates',
            'chat_history',
            'student_goal',
            'student_academic_record',
            'academic_metric',
            'analytics_result',
            'career_interest',
            'student_alert',
            'student_note',
            'teacher_assignment',
            'assignment',
            'assignment_submission'
        ]
        
        for table in tables_to_migrate:
            try:
                # Check if table exists in SQLite
                sq_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not sq_cursor.fetchone():
                    # print(f"Skipping {table} (not in SQLite)")
                    continue
                    
                # Get valid columns and their types from PostgreSQL
                pg_cursor.execute(
                    "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s", 
                    (table,)
                )
                pg_schema = {row[0]: row[1] for row in pg_cursor.fetchall()}
                pg_columns = list(pg_schema.keys())
                
                print(f"Migrating {table}...")
                
                # Get all data from SQLite
                sq_cursor.execute(f"SELECT * FROM {table}")
                rows = sq_cursor.fetchall()
                if not rows:
                    continue
                
                # Filter row data to only include valid PG columns
                sqlite_columns = rows[0].keys()
                common_columns = [col for col in sqlite_columns if col in pg_columns]
                
                if not common_columns:
                    print(f"No common columns for {table}, skipping.")
                    continue
                    
                placeholders = ', '.join(['%s'] * len(common_columns))
                col_names = ', '.join([f'"{c}"' for c in common_columns])
                query = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING"
                
                count = 0
                for row in rows:
                    # Create tuple of values for common columns only
                    values = []
                    for col in common_columns:
                        val = row[col]
                        # Handle Boolean conversion
                        if pg_schema[col] == 'boolean':
                            if val in (1, '1', True):
                                val = True
                            elif val in (0, '0', False):
                                val = False
                        values.append(val)
                    
                    pg_cursor.execute(query, tuple(values))
                    count += 1
                    
                pg_conn.commit() # Commit after each table
                print(f"Migrated {count} records for {table}.")
                
            except Exception as e:
                print(f"Error migrating {table}: {e}")
                pg_conn.rollback() # Rollback only this table's failure if possible, though previous commits should stay
                # note: rollback might roll back everything in current transaction blocks
                # With per-table commit, we start new transaction each time? Yes.
                # Don't abort the whole script on one table error, but rollback the specific failed statement if needed
                # Actually, in psycopg2, a failed transaction blocks everything. 
                # We should use savepoints or just let it fail and fix the script.
                # Re-raising to see the error, but with improved column handling this should likely succeed.
                raise e

        # 4. Reset Sequences (Crucial for Postgres auto-increment)
        print("\nResetting sequences...")
        tables_with_id = ['user', 'student_profile', 'teacher_profile'] + tables_to_migrate
        
        for table in tables_with_id:
            try:
                # Check if table exists in PG
                pg_cursor.execute(f"SELECT to_regclass('{table}')")
                if not pg_cursor.fetchone()[0]:
                    continue
                    
                pg_cursor.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(max(id), 1)) FROM {table}")
            except Exception as e:
                # Some tables might not have standard sequence names or IDs, ignore
                pass

        pg_conn.commit()
        print("\nMigration completed successfully!")

    except Exception as e:
        pg_conn.rollback()
        print(f"\nMigration FAILED: {e}")
        import traceback
        traceback.print_exc()

    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate_data()
