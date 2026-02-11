from flask import Blueprint, render_template, request, redirect, url_for, jsonify, make_response
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, TeacherProfile, StudentProfile, UserToken

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        if not email or not password or not role:
             return jsonify({"msg": "Missing fields"}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({"msg": "User already exists"}), 400

        # Create User
        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password_hash=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()

        # Create Profile based on role
        if role == 'teacher':
            new_teacher = TeacherProfile(user_id=new_user.id, full_name=name)
            db.session.add(new_teacher)
        elif role == 'student':
            new_student = StudentProfile(user_id=new_user.id, full_name=name)
            db.session.add(new_student)
            
        db.session.commit()

        return jsonify({"msg": "Registration successful", "email": email})

    # For GET requests, redirect to home page with auth anchor
    return redirect(url_for('home', _anchor='auth'))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        # role is not strictly needed for lookup as email is unique, but verification is good?
        
        user = User.query.filter_by(email=email).first()
        
        # Verify user exists and password is correct
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"msg": "Invalid credentials"}), 401

        # Verify role matches
        requested_role = request.form.get("role")
        if requested_role and user.role != requested_role:
            return jsonify({"msg": f"Access denied. You are registered as a {user.role}, please login with the correct role."}), 403

        # Create Token
        access_token = create_access_token(
            identity=str(user.id), # Use User ID as identity
            additional_claims={"role": user.role}
        )

        # Store Token in DB
        new_token = UserToken(user_id=user.id, access_token=access_token)
        db.session.add(new_token)
        db.session.commit()

        resp = jsonify({"msg": "Login successful", "role": user.role})
        set_access_cookies(resp, access_token)
        return resp

    # For GET requests, redirect to home page with auth anchor
    return redirect(url_for('home', _anchor='auth'))


@auth_bp.route("/logout")
def logout():
    """Clear JWT cookies and redirect to login page"""
    resp = make_response(redirect(url_for('auth.login', _anchor='login')))
    unset_jwt_cookies(resp)
    return resp
