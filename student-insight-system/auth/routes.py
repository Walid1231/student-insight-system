"""
auth/routes.py — Thin controllers for authentication.

Business logic extracted to services/auth_service.py.
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, make_response
from flask_jwt_extended import set_access_cookies, unset_jwt_cookies

from services.auth_service import AuthService
from core.errors import ConflictError, AuthorizationError, ValidationError

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

        try:
            result = AuthService.register_user(name, email, password, role)
            return jsonify(result)
        except ConflictError:
            return jsonify({"msg": "User already exists"}), 400
        except ValidationError as e:
            return jsonify({"msg": e.message}), 500

    return redirect(url_for('home', _anchor='auth'))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        requested_role = request.form.get("role")

        try:
            result = AuthService.login_user(email, password, requested_role)
        except AuthorizationError as e:
            status = 401 if "Invalid" in e.message else 403
            return jsonify({"msg": e.message}), status

        resp = jsonify({"msg": "Login successful", "role": result["role"]})
        set_access_cookies(resp, result["access_token"])
        return resp

    return redirect(url_for('home', _anchor='auth'))


@auth_bp.route("/logout")
def logout():
    """Clear JWT cookies and redirect to login page."""
    resp = make_response(redirect(url_for('auth.login', _anchor='login')))
    unset_jwt_cookies(resp)
    return resp
