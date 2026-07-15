from flask import Blueprint, jsonify, request
from sqlalchemy import func, extract, or_

from extensions import db, cache
from models import (
    User,
    StudentProfile,
    CompanyProfile,
    Drive,
    Application,
    ROLE_STUDENT,
    ROLE_COMPANY,
)
from utils.decorators import role_required
from utils.validators import ValidationError, validate_status_transition

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

DASHBOARD_CACHE_KEY = "admin:dashboard"
REPORTS_CACHE_KEY = "admin:reports"


def invalidate_admin_cache():
    cache.delete(DASHBOARD_CACHE_KEY)
    cache.delete(REPORTS_CACHE_KEY)
    cache.delete("drives:approved")


@admin_bp.get("/dashboard")
@role_required("admin")
def dashboard():
    cached = cache.get(DASHBOARD_CACHE_KEY)
    if cached is not None:
        return jsonify(cached), 200

    data = {
        "students": StudentProfile.query.count(),
        "companies": CompanyProfile.query.count(),
        "drives": Drive.query.count(),
        "applications": Application.query.count(),
    }
    cache.set(DASHBOARD_CACHE_KEY, data, timeout=300)
    return jsonify(data), 200


@admin_bp.get("/companies")
@role_required("admin")
def list_companies():
    q = request.args.get("q", "").strip()
    query = db.session.query(CompanyProfile).join(User)
    if q:
        query = query.filter(CompanyProfile.name.ilike(f"%{q}%"))
    companies = query.all()
    result = []
    for c in companies:
        d = c.to_dict()
        d["id"] = c.user_id
        d["active"] = c.user.active
        d["blacklisted"] = c.user.blacklisted
        d["email"] = c.user.email
        result.append(d)
    return jsonify(result), 200


@admin_bp.get("/students")
@role_required("admin")
def list_students():
    q = request.args.get("q", "").strip()
    query = db.session.query(StudentProfile).join(User)
    if q:
        query = query.filter(
            db.or_(StudentProfile.name.ilike(f"%{q}%"), User.email.ilike(f"%{q}%"))
        )
    students = query.all()
    result = []
    for s in students:
        d = s.to_dict()
        d["id"] = s.user_id
        d["active"] = s.user.active
        d["blacklisted"] = s.user.blacklisted
        d["email"] = s.user.email
        result.append(d)
    return jsonify(result), 200


@admin_bp.get("/drives")
@role_required("admin")
def list_drives():
    status = request.args.get("status", "").strip()
    query = Drive.query
    if status:
        query = query.filter_by(status=status)
    drives = query.order_by(Drive.created_at.desc()).all()
    return jsonify([d.to_dict() for d in drives]), 200


@admin_bp.post("/company/<int:user_id>/approve")
@role_required("admin")
def approve_company(user_id):
    company = CompanyProfile.query.filter_by(user_id=user_id).first_or_404()
    was_approved = company.approved
    company.approved = True
    db.session.commit()
    invalidate_admin_cache()
    # Notify the company only on the transition into "approved" (avoid re-sends).
    if not was_approved:
        from tasks import notify_company_approved
        notify_company_approved.delay(user_id)
    return jsonify({"message": "Company approved"}), 200


@admin_bp.post("/company/<int:user_id>/reject")
@role_required("admin")
def reject_company(user_id):
    company = CompanyProfile.query.filter_by(user_id=user_id).first_or_404()
    company.approved = False
    db.session.commit()
    invalidate_admin_cache()
    return jsonify({"message": "Company rejected"}), 200


@admin_bp.post("/drive/<int:drive_id>/approve")
@role_required("admin")
def approve_drive(drive_id):
    drive = Drive.query.get_or_404(drive_id)
    drive.status = "Approved"
    db.session.commit()
    invalidate_admin_cache()
    return jsonify({"message": "Drive approved"}), 200


@admin_bp.post("/drive/<int:drive_id>/reject")
@role_required("admin")
def reject_drive(drive_id):
    drive = Drive.query.get_or_404(drive_id)
    drive.status = "Rejected"
    db.session.commit()
    invalidate_admin_cache()
    return jsonify({"message": "Drive rejected"}), 200


@admin_bp.post("/user/<int:user_id>/blacklist")
@role_required("admin")
def blacklist_user(user_id):
    user = User.query.get_or_404(user_id)
    user.blacklisted = True
    # A blacklisted company's drives must disappear for students: revert any
    # Approved drives to Pending (they need admin re-approval if reinstated).
    if user.company_profile:
        Drive.query.filter(
            Drive.company_id == user.company_profile.id,
            Drive.status == "Approved",
        ).update({"status": "Pending"})
    db.session.commit()
    invalidate_admin_cache()
    return jsonify({"message": "User blacklisted"}), 200


@admin_bp.post("/user/<int:user_id>/deactivate")
@role_required("admin")
def deactivate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.active = False
    db.session.commit()
    invalidate_admin_cache()
    return jsonify({"message": "User deactivated"}), 200


@admin_bp.post("/user/<int:user_id>/activate")
@role_required("admin")
def activate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.active = True
    user.blacklisted = False
    db.session.commit()
    invalidate_admin_cache()
    return jsonify({"message": "User activated"}), 200


@admin_bp.get("/applications")
@role_required("admin")
def all_applications():
    query = Application.query
    q = request.args.get("q", "").strip()
    if q:
        like = f"%{q}%"
        query = (
            query.join(StudentProfile, Application.student_id == StudentProfile.id)
            .join(Drive, Application.drive_id == Drive.id)
            .join(CompanyProfile, Drive.company_id == CompanyProfile.id)
            .filter(
                or_(
                    StudentProfile.name.ilike(like),
                    Drive.title.ilike(like),
                    CompanyProfile.name.ilike(like),
                )
            )
        )
    apps = query.order_by(Application.applied_at.desc()).all()
    return jsonify([a.to_dict() for a in apps]), 200


@admin_bp.get("/reports")
@role_required("admin")
def reports():
    cached = cache.get(REPORTS_CACHE_KEY)
    if cached is not None:
        return jsonify(cached), 200

    drives_per_month = (
        db.session.query(
            extract("year", Drive.created_at).label("year"),
            extract("month", Drive.created_at).label("month"),
            func.count(Drive.id),
        )
        .group_by("year", "month")
        .order_by("year", "month")
        .all()
    )

    applications_by_status = (
        db.session.query(Application.status, func.count(Application.id))
        .group_by(Application.status)
        .all()
    )

    placements_per_company = (
        db.session.query(CompanyProfile.name, func.count(Application.id))
        .join(Drive, Drive.company_id == CompanyProfile.id)
        .join(Application, Application.drive_id == Drive.id)
        .filter(Application.status == "Selected")
        .group_by(CompanyProfile.name)
        .all()
    )

    data = {
        "drives_per_month": [
            {"year": int(y), "month": int(m), "count": c} for y, m, c in drives_per_month
        ],
        "applications_by_status": [{"status": s, "count": c} for s, c in applications_by_status],
        "placements_per_company": [{"company": n, "count": c} for n, c in placements_per_company],
    }
    cache.set(REPORTS_CACHE_KEY, data, timeout=300)
    return jsonify(data), 200
