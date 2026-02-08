from flask import Blueprint, render_template, request, redirect, url_for, jsonify, make_response
from flask_jwt_extended import create_access_token, set_access_cookies
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Handle both JSON and Form data for flexibility
        if request.is_json:
            data = request.get_json()
            name = data.get("name")
            email = data.get("email")
            password = data.get("password")
            role = data.get("role")
        else:
            name = request.form.get("name")
            email = request.form.get("email")
            password = request.form.get("password")
            role = request.form.get("role")

        if not email or not password:
            return jsonify({"msg": "Email and password are required"}), 400

        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({"msg": "User already exists"}), 400

        # Hash password
        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name, 
            email=email, 
            password=hashed_password, 
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        return jsonify({"msg": "Registration successful", "email": email}), 201

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.is_json:
            data = request.get_json()
            email = data.get("email")
            password = data.get("password")
        else:
            email = request.form.get("email")
            password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            return jsonify({"msg": "Invalid credentials"}), 401

        access_token = create_access_token(
            identity=user.email,
            additional_claims={"role": user.role, "name": user.name}
        )

        resp = jsonify({"msg": "Login successful", "role": user.role})
        set_access_cookies(resp, access_token)
        return resp, 200

    return render_template("register.html")


@auth_bp.route("/logout")
def logout():
    resp = make_response(redirect(url_for("auth.login")))
    resp.set_cookie("access_token_cookie", "", expires=0)
    return resp
