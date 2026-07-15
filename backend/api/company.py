from flask import Blueprint, jsonify, request

from extensions import db, cache
from models import Drive, Application, OfferLetter
from utils.decorators import role_required, current_user
from utils.validators import (
    validate_non_empty,
    validate_cgpa,
    validate_deadline,
    validate_branches_list,
    validate_years_list,
    validate_status_transition,
)
from utils.offer_letter import generate_offer_letter_pdf
from api.admin import invalidate_admin_cache

company_bp = Blueprint("company", __name__, url_prefix="/api/company")


def _drive_belongs_to(drive, company_profile):
    return drive.company_id == company_profile.id


@company_bp.get("/dashboard")
@role_required("company")
def dashboard():
    user = current_user()
    company = user.company_profile

    drives = Drive.query.filter_by(company_id=company.id).order_by(Drive.created_at.desc()).all()
    drive_data = []
    for d in drives:
        count = Application.query.filter_by(drive_id=d.id).count()
        drive_data.append(d.to_dict(applicant_count=count))

    return jsonify({"profile": company.to_dict(), "drives": drive_data}), 200


@company_bp.post("/drive")
@role_required("company")
def create_drive():
    user = current_user()
    company = user.company_profile

    if not company.approved:
        return jsonify({"errors": {"company": "Your company must be approved before creating drives"}}), 403

    payload = request.get_json(silent=True) or {}
    errors = {}

    title = validate_non_empty(payload.get("title"), errors, "title", "Job title")
    description = validate_non_empty(payload.get("description"), errors, "description", "Description")
    branches = validate_branches_list(payload.get("eligible_branches"), errors)
    min_cgpa = validate_cgpa(payload.get("min_cgpa"), errors, field="min_cgpa")
    years = validate_years_list(payload.get("eligible_years"), errors)
    deadline = validate_deadline(payload.get("deadline"), errors)

    if errors:
        return jsonify({"errors": errors}), 422

    drive = Drive(
        company_id=company.id,
        title=title,
        description=description,
        eligible_branches=",".join(branches),
        min_cgpa=min_cgpa,
        eligible_years=",".join(str(y) for y in years),
        deadline=deadline,
        status="Pending",
    )
    db.session.add(drive)
    db.session.commit()
    invalidate_admin_cache()

    return jsonify(drive.to_dict()), 201


@company_bp.put("/drive/<int:drive_id>")
@role_required("company")
def update_drive(drive_id):
    user = current_user()
    drive = Drive.query.get_or_404(drive_id)
    if not _drive_belongs_to(drive, user.company_profile):
        return jsonify({"message": "Forbidden"}), 403

    payload = request.get_json(silent=True) or {}
    errors = {}

    title = validate_non_empty(payload.get("title"), errors, "title", "Job title")
    description = validate_non_empty(payload.get("description"), errors, "description", "Description")
    branches = validate_branches_list(payload.get("eligible_branches"), errors)
    min_cgpa = validate_cgpa(payload.get("min_cgpa"), errors, field="min_cgpa")
    years = validate_years_list(payload.get("eligible_years"), errors)
    deadline = validate_deadline(payload.get("deadline"), errors)

    if errors:
        return jsonify({"errors": errors}), 422

    drive.title = title
    drive.description = description
    drive.eligible_branches = ",".join(branches)
    drive.min_cgpa = min_cgpa
    drive.eligible_years = ",".join(str(y) for y in years)
    drive.deadline = deadline
    # Editing sends it back for re-approval.
    drive.status = "Pending"
    db.session.commit()
    invalidate_admin_cache()

    return jsonify(drive.to_dict()), 200


@company_bp.post("/drive/<int:drive_id>/close")
@role_required("company")
def close_drive(drive_id):
    user = current_user()
    drive = Drive.query.get_or_404(drive_id)
    if not _drive_belongs_to(drive, user.company_profile):
        return jsonify({"message": "Forbidden"}), 403

    drive.status = "Closed"
    db.session.commit()
    invalidate_admin_cache()
    return jsonify({"message": "Drive closed"}), 200


@company_bp.get("/drive/<int:drive_id>/applicants")
@role_required("company")
def drive_applicants(drive_id):
    user = current_user()
    drive = Drive.query.get_or_404(drive_id)
    if not _drive_belongs_to(drive, user.company_profile):
        return jsonify({"message": "Forbidden"}), 403

    apps = Application.query.filter_by(drive_id=drive_id).order_by(Application.applied_at.desc()).all()
    return jsonify([a.to_dict() for a in apps]), 200


@company_bp.put("/application/<int:application_id>")
@role_required("company")
def update_application(application_id):
    user = current_user()
    application = Application.query.get_or_404(application_id)
    if not _drive_belongs_to(application.drive, user.company_profile):
        return jsonify({"message": "Forbidden"}), 403

    payload = request.get_json(silent=True) or {}
    errors = {}

    new_status = payload.get("status")
    if new_status and new_status != application.status:
        if not validate_status_transition(application.status, new_status, errors):
            return jsonify({"errors": errors}), 422
        application.status = new_status

    interview_changed = False
    if "interview_datetime" in payload and payload["interview_datetime"]:
        from datetime import datetime

        try:
            new_dt = datetime.fromisoformat(payload["interview_datetime"])
        except ValueError:
            return jsonify({"errors": {"interview_datetime": "Invalid date/time format"}}), 422
        interview_changed = application.interview_datetime != new_dt
        application.interview_datetime = new_dt

    if "remarks" in payload:
        application.remarks = payload["remarks"]

    db.session.commit()
    invalidate_admin_cache()
    # Notify the student immediately when an interview is newly scheduled or moved.
    if interview_changed:
        from tasks import notify_interview_scheduled
        notify_interview_scheduled.delay(application.id)
    return jsonify(application.to_dict()), 200


@company_bp.post("/application/<int:application_id>/offer-letter")
@role_required("company")
def generate_offer_letter(application_id):
    user = current_user()
    application = Application.query.get_or_404(application_id)
    if not _drive_belongs_to(application.drive, user.company_profile):
        return jsonify({"message": "Forbidden"}), 403

    if application.status != "Selected":
        return jsonify({"errors": {"status": "Offer letters can only be generated for Selected applicants"}}), 422

    if application.offer_letter:
        return jsonify(application.offer_letter.to_dict()), 200

    file_path = generate_offer_letter_pdf(application)
    offer_letter = OfferLetter(application_id=application.id, file_path=file_path)
    db.session.add(offer_letter)
    db.session.commit()

    return jsonify(offer_letter.to_dict()), 201


@company_bp.post("/application/<int:application_id>/offer-letter/email")
@role_required("company")
def email_offer_letter_to_student(application_id):
    user = current_user()
    application = Application.query.get_or_404(application_id)
    if not _drive_belongs_to(application.drive, user.company_profile):
        return jsonify({"message": "Forbidden"}), 403

    if not application.offer_letter:
        return jsonify({"errors": {"offer_letter": "Generate the offer letter first"}}), 422

    from tasks import email_offer_letter

    email_offer_letter.delay(application.id)
    return jsonify({"message": "Offer letter is being emailed to the student"}), 202
