import sys
sys.path.insert(0, '.')
from app import app
from models import db

with app.app_context():
    # Fix the 'user' table - it needs quoting since 'user' is a reserved word in PG
    max_id = db.session.execute(db.text('SELECT COALESCE(MAX(id), 0) FROM "user"')).scalar()
    seq = db.session.execute(db.text("SELECT pg_get_serial_sequence('\"user\"', 'id')")).scalar()
    if seq:
        db.session.execute(db.text("SELECT setval(:seq, :val, false)"), {"seq": seq, "val": max_id + 1})
        db.session.commit()
        print(f"user table: sequence reset to {max_id + 1}")
    else:
        print("No sequence found for user table")
    
    # Verify registration works end-to-end
    from models import User, StudentProfile
    from werkzeug.security import generate_password_hash
    
    test_user = User(email="verify_reg@test.com", password_hash=generate_password_hash("pass"), role="student")
    db.session.add(test_user)
    db.session.commit()
    
    test_profile = StudentProfile(user_id=test_user.id, full_name="Verify Registration")
    db.session.add(test_profile)
    db.session.commit()
    
    print(f"Registration test: User id={test_user.id}, Profile id={test_profile.id} - SUCCESS!")
    
    # Clean up
    db.session.delete(test_profile)
    db.session.delete(test_user)
    db.session.commit()
    print("Cleanup done. Registration is working!")
