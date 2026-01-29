from flask import Flask, render_template
from flask_jwt_extended import JWTManager

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    JWTManager(app)

    from auth.routes import auth_bp
    from dashboard.routes import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)

    @app.route("/")
    def home():
        return render_template("home.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
