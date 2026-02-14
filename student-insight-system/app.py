from flask import Flask, render_template
from config import Config
from models import db
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from auth.routes import auth_bp
from dashboard.routes import dashboard_bp
import os
import time

app = Flask(__name__)
app.config.from_object(Config)

# Disable caching for static files during development
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Initialize Extensions
db.init_app(app)
migrate = Migrate(app, db)  # Enables 'flask db' commands for migrations
jwt = JWTManager(app)
CORS(app)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)

# Add cache-busting version to all templates
@app.context_processor
def inject_css_version():
    """Inject a timestamp-based version for cache busting"""
    return {'css_version': int(time.time())}

# Add cache control headers to all responses
@app.after_request
def add_header(response):
    """Add headers to prevent caching during development"""
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

# Landing Page
@app.route("/")
def home():
    return render_template("home.html")

if __name__ == "__main__":
    with app.app_context():
        # Test the database connection
        try:
            db.create_all()
            print("=" * 60)
            print("[SUCCESS] Connected to PostgreSQL database!")
            print("   Database: student_insight_system")
            print("   Host: localhost:5432")
            print("=" * 60)
        except Exception as e:
            print("=" * 60)
            print("[ERROR] Database connection failed!")
            print(f"   Error: {e}")
            print("=" * 60)
            print("\nTroubleshooting tips:")
            print("1. Make sure PostgreSQL is running")
            print("2. Check your password in config.py")
            print("3. Verify database 'student_insight_system' exists")
            print("4. Confirm PostgreSQL is on port 5432")
            print("=" * 60)
    
    app.run(debug=True)