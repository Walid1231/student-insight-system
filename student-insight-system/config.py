class Config:
    SECRET_KEY = "super-secret-key"
    JWT_SECRET_KEY = "jwt-secret-key"
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = False  # Set to True in production with HTTPS
    JWT_COOKIE_CSRF_PROTECT = False  # Disable for simpler form handling
    GEMINI_API_KEY = "AIzaSyCOF5Zibr5i-TLHJsJO9O2YYPKEGcX4IqA"
    
    # Database Configuration
    import os
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'student_insight.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
