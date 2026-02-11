from app import app
from models import db, User
from werkzeug.security import check_password_hash

with app.app_context():
    users = User.query.all()
    print(f"Total users: {len(users)}")
    print("-" * 60)
    print(f"{'ID':<5} {'Email':<30} {'Role':<10} {'Password Hash (Prefix)':<20}")
    print("-" * 60)
    for u in users:
        print(f"{u.id:<5} {u.email:<30} {u.role:<10} {u.password_hash[:20]}...")
    
    print("\n--- Verifying Test Users ---")
    teacher = User.query.filter_by(email='teacher@test.com').first()
    if teacher:
        print(f"\nChecking 'teacher@test.com': Role='{teacher.role}'")
        is_valid = check_password_hash(teacher.password_hash, 'password')
        print(f"Password 'password' valid? {is_valid}")
    else:
        print("\n'teacher@test.com' not found.")

    # Check a student
    student = User.query.filter(User.role == 'student').first()
    if student:
        print(f"\nChecking student '{student.email}': Role='{student.role}'")
        is_valid = check_password_hash(student.password_hash, 'password')
        print(f"Password 'password' valid? {is_valid}")
