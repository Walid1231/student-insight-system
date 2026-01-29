from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_jwt_extended import create_access_token

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        role = request.form.get("role")

        # DB save will come later

        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")

        # TEMP role (later from DB)
        role = "student" if "student" in email else "teacher"

        access_token = create_access_token(
            identity=email,
            additional_claims={"role": role}
        )

        return jsonify(access_token=access_token, role=role)

    return render_template("login.html")
