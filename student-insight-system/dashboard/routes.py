from flask import Blueprint, render_template, jsonify
from flask_jwt_extended import jwt_required, get_jwt

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/student/dashboard")
@jwt_required()
def student_dashboard():
    claims = get_jwt()
    role = claims.get("role")

    if role != "student":
        return jsonify({"msg": "Access denied"}), 403

    return render_template("student_dashboard.html")


@dashboard_bp.route("/teacher/dashboard")
@jwt_required()
def teacher_dashboard():
    claims = get_jwt()
    role = claims.get("role")

    if role != "teacher":
        return jsonify({"msg": "Access denied"}), 403

    return render_template("teacher_dashboard.html")
