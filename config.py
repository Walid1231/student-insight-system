import os
from datetime import timedelta

class Config:
    # Get the absolute path of the directory containing this file
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Security Keys
    SECRET_KEY = "super-secret-key"  # Change this in production
    JWT_SECRET_KEY = "jwt-secret-key" # Change this in production
    
    # JWT Configuration
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = False  # Set to True in production (HTTPS)
    JWT_COOKIE_CSRF_PROTECT = False  # Disabled for easier testing, enable in prod
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7) # Long expiration for development
    
    # Database Configuration
    # Creates the DB in the 'instance' folder
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'student_insight_v2.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Keys
    GEMINI_API_KEY = ""