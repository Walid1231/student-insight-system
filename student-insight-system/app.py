from flask import Flask, render_template
from config import Config
from models import db
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from auth.routes import auth_bp
from dashboard.routes import dashboard_bp
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize Extensions
db.init_app(app)
jwt = JWTManager(app)
CORS(app)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)

# Landing Page
@app.route("/")
def home():
    return render_template("home.html")

if __name__ == "__main__":
    with app.app_context():
        from models import db
        db.create_all()
        print("Database tables created.")  # Ensure tables exist
    app.run(debug=True)