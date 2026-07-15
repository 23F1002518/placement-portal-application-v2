from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token

from extensions import db
from models import User, StudentProfile, CompanyProfile, ROLE_STUDENT, ROLE_COMPANY
from utils.decorators import current_user
from utils.validators import (
    ValidationError,
    validate_email,
    validate_password,
    validate_non_empty,
    validate_cgpa,
    validate_graduation_year,
    validate_phone,
    validate_branch,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api")


@auth_bp.post("/register/student")
def register_student():
    payload = request.get_json(silent=True) or {}
    errors = {}

    email = validate_email(payload.get("email"), errors)
    password = validate_password(payload.get("password"), errors)
    name = validate_non_empty(payload.get("name"), errors, "name", "Name")
    branch = validate_branch(payload.get("branch"), errors)
    cgpa = validate_cgpa(payload.get("cgpa"), errors)
    graduation_year = validate_graduation_year(payload.get("graduation_year"), errors)
    phone = validate_phone(payload.get("phone"), errors)

    if email and User.query.filter_by(email=email).first():
        errors.setdefault("email", "An account with this email already exists")

    if errors:
        return jsonify({"errors": errors}), 422

    user = User(email=email, role=ROLE_STUDENT)
    user.set_password(password)
    user.student_profile = StudentProfile(
        name=name,
        branch=branch,
        cgpa=cgpa,
        graduation_year=graduation_year,
        phone=phone,
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Registration successful. You can now log in."}), 201


@auth_bp.post("/register/company")
def register_company():
    payload = request.get_json(silent=True) or {}
    errors = {}

    email = validate_email(payload.get("email"), errors)
    password = validate_password(payload.get("password"), errors)
    name = validate_non_empty(payload.get("name"), errors, "name", "Company name")
    hr_contact = validate_non_empty(payload.get("hr_contact"), errors, "hr_contact", "HR contact")
    website = payload.get("website") or None
    description = payload.get("description") or None

    if email and User.query.filter_by(email=email).first():
        errors.setdefault("email", "An account with this email already exists")

    if errors:
        return jsonify({"errors": errors}), 422

    user = User(email=email, role=ROLE_COMPANY)
    user.set_password(password)
    user.company_profile = CompanyProfile(
        name=name,
        hr_contact=hr_contact,
        website=website,
        description=description,
        approved=False,
    )
    db.session.add(user)
    db.session.commit()

    return (
        jsonify({"message": "Registration submitted. Await admin approval before logging in."}),
        201,
    )


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    errors = {}

    email = validate_non_empty(payload.get("email"), errors, "email", "Email")
    password = validate_non_empty(payload.get("password"), errors, "password", "Password")
    if errors:
        return jsonify({"errors": errors}), 422

    user = User.query.filter_by(email=email.strip().lower()).first()
    if not user or not user.check_password(password):
        return jsonify({"errors": {"password": "Invalid email or password"}}), 401

    if user.blacklisted:
        return jsonify({"errors": {"email": "This account has been blacklisted"}}), 403
    if not user.active:
        return jsonify({"errors": {"email": "This account has been deactivated"}}), 403
    if user.role == ROLE_COMPANY and not user.company_profile.approved:
        return jsonify({"errors": {"email": "Company registration is pending admin approval"}}), 403

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify({"token": token, "user": user.to_dict()}), 200


@auth_bp.get("/me")
def me():
    from flask_jwt_extended import verify_jwt_in_request

    verify_jwt_in_request()
    user = current_user()
    if not user:
        return jsonify({"message": "User not found"}), 404
    return jsonify(user.to_dict()), 200
