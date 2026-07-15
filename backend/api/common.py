import os
from datetime import date

from flask import Blueprint, jsonify, request, send_from_directory, current_app
from flask_jwt_extended import get_jwt

from extensions import cache
from models import Drive, Application, StudentProfile, CompanyProfile, User
from utils.decorators import login_required, current_user

common_bp = Blueprint("common", __name__, url_prefix="/api")

APPROVED_DRIVES_CACHE_KEY = "drives:approved"


def _get_approved_open_drives():
    cached = cache.get(APPROVED_DRIVES_CACHE_KEY)
    if cached is not None:
        return cached

    drives = (
        Drive.query.join(CompanyProfile, Drive.company_id == CompanyProfile.id)
        .join(User, CompanyProfile.user_id == User.id)
        .filter(
            Drive.status == "Approved",
            Drive.deadline >= date.today(),
            User.blacklisted.is_(False),
            User.active.is_(True),
        )
        .all()
    )
    data = [d.to_dict() for d in drives]
    cache.set(APPROVED_DRIVES_CACHE_KEY, data, timeout=120)
    return data


@common_bp.get("/drives")
@login_required
def list_drives():
    q = request.args.get("q", "").strip().lower()
    branch = request.args.get("branch", "").strip()
    min_cgpa = request.args.get("min_cgpa", type=float)

    drives = _get_approved_open_drives()

    if q:
        drives = [
            d for d in drives if q in d["title"].lower() or q in (d["company_name"] or "").lower()
        ]
    if branch:
        drives = [d for d in drives if branch in d["eligible_branches"]]
    if min_cgpa is not None:
        drives = [d for d in drives if d["min_cgpa"] <= min_cgpa]

    return jsonify(drives), 200


@common_bp.get("/offer-letter/<int:application_id>")
@login_required
def download_offer_letter(application_id):
    application = Application.query.get_or_404(application_id)
    if not application.offer_letter:
        return jsonify({"message": "Not found"}), 404

    claims = get_jwt()
    user = current_user()
    role = claims.get("role")

    if role == "company" and application.drive.company_id != user.company_profile.id:
        return jsonify({"message": "Forbidden"}), 403
    if role == "student" and application.student_id != user.student_profile.id:
        return jsonify({"message": "Forbidden"}), 403
    if role not in ("company", "student"):
        return jsonify({"message": "Forbidden"}), 403

    directory = current_app.config["OFFER_LETTER_DIR"]
    filename = os.path.basename(application.offer_letter.file_path)
    return send_from_directory(directory, filename, as_attachment=True)


@common_bp.get("/resume/<int:student_user_id>")
@login_required
def download_resume(student_user_id):
    student = StudentProfile.query.filter_by(user_id=student_user_id).first_or_404()
    if not student.resume_path:
        return jsonify({"message": "No resume uploaded"}), 404

    claims = get_jwt()
    user = current_user()
    role = claims.get("role")

    if role == "student" and student.user_id != user.id:
        return jsonify({"message": "Forbidden"}), 403
    if role == "company":
        has_application = (
            Application.query.join(Drive)
            .filter(Application.student_id == student.id, Drive.company_id == user.company_profile.id)
            .first()
        )
        if not has_application:
            return jsonify({"message": "Forbidden"}), 403
    if role not in ("student", "company", "admin"):
        return jsonify({"message": "Forbidden"}), 403

    directory = current_app.config["RESUME_DIR"]
    filename = os.path.basename(student.resume_path)
    return send_from_directory(directory, filename, as_attachment=True)
