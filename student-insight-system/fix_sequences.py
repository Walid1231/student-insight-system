"""Fix PostgreSQL sequences after SQLite migration."""
import sys
sys.path.insert(0, '.')
from app import app
from models import db

with app.app_context():
    result = db.session.execute(db.text(
        "SELECT c.relname, a.attname, pg_get_serial_sequence(c.relname::text, a.attname::text) "
        "FROM pg_class c "
        "JOIN pg_attribute a ON a.attrelid = c.oid "
        "JOIN pg_attrdef d ON d.adrelid = c.oid AND d.adnum = a.attnum "
        "WHERE c.relkind = 'r' AND a.attname = 'id' "
        "AND pg_get_serial_sequence(c.relname::text, a.attname::text) IS NOT NULL "
        "ORDER BY c.relname"
    ))
    
    for row in result:
        table, col, seq = row[0], row[1], row[2]
        try:
            max_id = db.session.execute(db.text(f"SELECT COALESCE(MAX(id), 0) FROM {table}")).scalar()
            new_val = max_id + 1
            db.session.execute(db.text(f"SELECT setval(:seq, :val, false)"), {"seq": seq, "val": new_val})
            print(f"  {table}: sequence reset to {new_val} (max id was {max_id})")
        except Exception as e:
            print(f"  {table}: ERROR - {e}")
            db.session.rollback()
    
    db.session.commit()
    print("\nAll sequences fixed!")
    
    # Quick test: try inserting and rolling back
    from models import User, StudentProfile
    from werkzeug.security import generate_password_hash
    
    test_user = User(email="__seq_test__@test.com", password_hash=generate_password_hash("test"), role="student")
    db.session.add(test_user)
    db.session.flush()
    
    test_profile = StudentProfile(user_id=test_user.id, full_name="Sequence Test")
    db.session.add(test_profile)
    db.session.flush()
    print(f"\nVerification: User id={test_user.id}, Profile id={test_profile.id} - OK!")
    
    db.session.rollback()
    print("Test rolled back. Registration should work now.")
