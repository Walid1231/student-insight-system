from flask import Blueprint, render_template, request, redirect, url_for, jsonify, make_response
from flask_jwt_extended import create_access_token, set_access_cookies

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        role = request.form.get("role")

        db.session.add(new_user)
        db.session.commit()

        return jsonify({"msg": "Registration successful", "email": email})

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        role = request.form.get("role")  # Use role from form

        access_token = create_access_token(
            identity=email,
            additional_claims={"role": role}
        )

        resp = jsonify({"msg": "Login successful", "role": role})
        set_access_cookies(resp, access_token)
        return resp

    return render_template("register.html")
