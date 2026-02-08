import os
from flask import Flask, render_template, request
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config
from models import db, User  # IMPORT YOUR MODELS HERE so SQLAlchemy knows about them
from auth.routes import auth_bp
from dashboard.routes import dashboard_bp

# Create Flask app
app = Flask(__name__)

# -------------------------
# CONFIGURATION
# -------------------------
# Load configuration from the Config class in config.py
app.config.from_object(Config)

# -------------------------
# INITIALIZE EXTENSIONS
# -------------------------
db.init_app(app)
jwt = JWTManager(app)
CORS(app)

# -------------------------
# REGISTER BLUEPRINTS
# -------------------------
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)

# -------------------------
# CONTEXT PROCESSORS
# -------------------------
@app.context_processor
def inject_sidebar_state():
    sidebar_cookie = request.cookies.get('sidebar_collapsed', 'false')
    return dict(sidebar_collapsed=sidebar_cookie)


# -------------------------
# ROUTES
# -------------------------
@app.route("/")
def home():
    return render_template("home.html")

# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":
    with app.app_context():
        # Ensure 'instance' folder exists for SQLite DB
        if not os.path.exists(os.path.join(app.root_path, 'instance')):
            os.makedirs(os.path.join(app.root_path, 'instance'))
            
        db.create_all()  # Creates tables based on imported models
        print("Database initialized successfully.")
        
    app.run(debug=True)