class Config:
    SECRET_KEY = "super-secret-key"
    JWT_SECRET_KEY = "jwt-secret-key"
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = False  # Set to True in production with HTTPS
    JWT_COOKIE_CSRF_PROTECT = False  # Disable for simpler form handling
    from datetime import timedelta
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7) # Long expiration for development
    GEMINI_API_KEY = "AIzaSyCOF5Zibr5i-TLHJsJO9O2YYPKEGcX4IqA"
    
    # -------------------------
    # DATABASE CONFIGURATION
    # -------------------------
    # PostgreSQL Connection String
    # Format: postgresql://username:password@host:port/database_name
    # 
    # IMPORTANT: Replace 'YOUR_DB_PASSWORD' with your actual PostgreSQL password
    # If you didn't set a password during installation, try removing ':YOUR_DB_PASSWORD'
    # 
    # Connection Details:
    # - Username: postgres (default PostgreSQL username)
    # - Password: YOUR_DB_PASSWORD (replace with your actual password)
    # - Host: localhost (database is running on your local machine)
    # - Port: 5432 (default PostgreSQL port)
    # - Database: student_insight_system (the database you created)
    
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:12345@localhost:5432/student_insight_system'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Optional: Uncomment below to use SQLite for testing
    # import os
    # BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    # SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'student_insight.db')}"
