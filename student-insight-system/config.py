class Config:
    SECRET_KEY = "super-secret-key"
    JWT_SECRET_KEY = "jwt-secret-key"
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = False  # Set to True in production with HTTPS
    JWT_COOKIE_CSRF_PROTECT = False  # Disable for simpler form handling
    GEMINI_API_KEY = "AIzaSyAghJuMcqMfBOxLAhgZ0yGbgyKbfVTC8VU"
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///student_insight.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
