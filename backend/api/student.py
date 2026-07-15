import os

from flask import Blueprint, jsonify, request, send_from_directory, current_app
from werkzeug.utils import secure_filename

from extensions import db
from models import Drive, Application
from utils.decorators import role_required, current_user
from utils.validators import (
    validate_non_empty,
    validate_cgpa,
    validate_graduation_year,
    validate_phone,
    validate_branch,
    validate_resume_file,
    validate_eligibility,
    validate_drive_open,
    validate_no_duplicate_application,
)
from api.common import _get_approved_open_drives

student_bp = Blueprint("student", __name__, url_prefix="/api/student")


@student_bp.get("/dashboard")
@role_required("student")
def dashboard():
    user = current_user()
    student = user.student_profile

    drives = _get_approved_open_drives()
    applied_ids = {a.drive_id for a in student.applications}

    for d in drives:
        d["applied"] = d["id"] in applied_ids
        d["eligible"] = (
            student.branch in d["eligible_branches"]
            and student.cgpa >= d["min_cgpa"]
            and student.graduation_year in d["eligible_years"]
        )

    return jsonify({"profile": student.to_dict(), "drives": drives}), 200


@student_bp.post("/drive/<int:drive_id>/apply")
@role_required("student")
def apply(drive_id):
    user = current_user()
    student = user.student_profile
    drive = Drive.query.get_or_404(drive_id)

    errors = {}
    if not validate_drive_open(drive, errors):
        return jsonify({"errors": errors}), 422
    if not validate_eligibility(student, drive, errors):
        return jsonify({"errors": errors}), 422

    exists = Application.query.filter_by(student_id=student.id, drive_id=drive_id).first()
    if not validate_no_duplicate_application(exists, errors):
        return jsonify({"errors": errors}), 422

    application = Application(student_id=student.id, drive_id=drive_id, status="Applied")
    db.session.add(application)
    db.session.commit()

    return jsonify(application.to_dict()), 201


@student_bp.get("/applications")
@role_required("student")
def applications():
    user = current_user()
    student = user.student_profile
    query = Application.query.filter_by(student_id=student.id)
    status = request.args.get("status", "").strip()
    if status:
        query = query.filter_by(status=status)
    apps = query.order_by(Application.applied_at.desc()).all()
    return jsonify([a.to_dict() for a in apps]), 200


@student_bp.put("/profile")
@role_required("student")
def update_profile():
    user = current_user()
    student = user.student_profile
    payload = request.get_json(silent=True) or {}
    errors = {}

    name = validate_non_empty(payload.get("name"), errors, "name", "Name")
    branch = validate_branch(payload.get("branch"), errors)
    cgpa = validate_cgpa(payload.get("cgpa"), errors)
    graduation_year = validate_graduation_year(payload.get("graduation_year"), errors)
    phone = validate_phone(payload.get("phone"), errors)

    if errors:
        return jsonify({"errors": errors}), 422

    student.name = name
    student.branch = branch
    student.cgpa = cgpa
    student.graduation_year = graduation_year
    student.phone = phone
    db.session.commit()

    return jsonify(student.to_dict()), 200


@student_bp.post("/resume")
@role_required("student")
def upload_resume():
    user = current_user()
    student = user.student_profile
    errors = {}

    file_storage = request.files.get("resume")
    validated = validate_resume_file(file_storage, errors)
    if errors:
        return jsonify({"errors": errors}), 422

    resume_dir = current_app.config["RESUME_DIR"]
    os.makedirs(resume_dir, exist_ok=True)
    ext = validated.filename.rsplit(".", 1)[-1].lower()
    filename = secure_filename(f"resume_user{user.id}.{ext}")
    validated.save(os.path.join(resume_dir, filename))

    student.resume_path = os.path.join("uploads", "resumes", filename)
    db.session.commit()

    return jsonify(student.to_dict()), 200


@student_bp.post("/export")
@role_required("student")
def trigger_export():
    from tasks import export_applications_csv

    user = current_user()
    task = export_applications_csv.delay(user.id)
    return jsonify({"task_id": task.id}), 202


@student_bp.get("/export/<task_id>")
@role_required("student")
def export_status(task_id):
    from tasks import export_applications_csv

    result = export_applications_csv.AsyncResult(task_id)
    if result.state == "PENDING":
        return jsonify({"state": result.state}), 200
    if result.state == "FAILURE":
        return jsonify({"state": result.state, "error": str(result.info)}), 200

    payload = {"state": result.state}
    if result.state == "SUCCESS" and isinstance(result.result, dict):
        payload["result"] = result.result
    return jsonify(payload), 200


@student_bp.get("/export/download/<path:filename>")
@role_required("student")
def download_export(filename):
    user = current_user()
    # The client may pass a bare filename or the stored relative path
    # (uploads/exports/<name>); reduce to the basename so the ownership check and
    # send_from_directory both see just the file (also blocks path traversal).
    filename = os.path.basename(filename)
    # Exports are named export_user<id>_<taskid>.csv — only the owning student may download.
    if not filename.startswith(f"export_user{user.id}_"):
        return jsonify({"message": "Forbidden"}), 403

    return send_from_directory(current_app.config["EXPORT_DIR"], filename, as_attachment=True)
