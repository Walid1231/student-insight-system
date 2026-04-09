"""
auth/routes.py — Thin controllers for authentication.

Business logic extracted to services/auth_service.py.
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, make_response
from flask_jwt_extended import set_access_cookies, unset_jwt_cookies, verify_jwt_in_request, get_jwt

from services.auth_service import AuthService
from core.errors import ConflictError, AuthorizationError, ValidationError

auth_bp = Blueprint("auth", __name__)


def _redirect_if_authenticated():
    """If the user has a valid JWT, redirect to their dashboard. Returns None if not authenticated."""
    try:
        verify_jwt_in_request(optional=True)
        claims = get_jwt()
        role = claims.get("role")
        if role == "student":
            return redirect(url_for("dashboard.student_dashboard"))
        elif role == "teacher":
            return redirect(url_for("teacher.teacher_dashboard"))
    except Exception:
        pass
    return None


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
        except ConflictError as e:
            return jsonify({"msg": e.message}), 400
        except ValidationError as e:
            return jsonify({"msg": e.message}), 500

    # GET — redirect authenticated users to their dashboard
    redir = _redirect_if_authenticated()
    if redir:
        return redir
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

    # GET — redirect authenticated users to their dashboard
    redir = _redirect_if_authenticated()
    if redir:
        return redir
    return redirect(url_for('home', _anchor='auth'))


@auth_bp.route("/logout")
def logout():
    """Clear JWT cookies and redirect to home page."""
    resp = make_response(redirect(url_for('home')))
    # Explicitly delete the JWT cookie(s) — belt-and-suspenders
    unset_jwt_cookies(resp)
    resp.delete_cookie("access_token_cookie", path="/")
    resp.delete_cookie("csrf_access_token", path="/")
    # Prevent browser from caching the old auth state
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        AuthService.request_password_reset(email)
        # Always show the same message for privacy
        return render_template("forgot_password.html", submitted=True)
    return render_template("forgot_password.html", submitted=False)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    # Validate token on GET
    token_obj = AuthService.validate_reset_token(token)
    if not token_obj:
        return render_template("reset_password.html", invalid=True, token=token)

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if len(password) < 6:
            return render_template("reset_password.html", invalid=False, token=token,
                                   error="Password must be at least 6 characters.")

        if password != confirm:
            return render_template("reset_password.html", invalid=False, token=token,
                                   error="Passwords do not match.")

        try:
            AuthService.reset_password(token, password)
            return render_template("reset_password.html", success=True, token=token)
        except Exception as e:
            return render_template("reset_password.html", invalid=True, token=token)

    return render_template("reset_password.html", invalid=False, token=token)
