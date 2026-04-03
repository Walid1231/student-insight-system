from app import create_app
from models import User

app = create_app()
with app.app_context():
    user = User.query.filter_by(email="teacher@test.com").first()
    if user:
        print(f"FOUND: {user.email}, Role: {user.role}")
    else:
        print("NOT FOUND: teacher@test.com")
    
    # List all users for sanity
    print("\nAll users:")
    users = User.query.all()
    for u in users:
        print(f" - {u.email} ({u.role})")
