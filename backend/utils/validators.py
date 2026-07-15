import re
from datetime import date, datetime

from flask import current_app

from models import APPLICATION_TRANSITIONS

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,}$")
PHONE_RE = re.compile(r"^\d{10}$")

CURRENT_YEAR = datetime.utcnow().year


class ValidationError(Exception):
    """Raised with a dict of field -> message errors."""

    def __init__(self, errors):
        super().__init__("Validation failed")
        self.errors = errors


def add_error(errors, field, message):
    errors.setdefault(field, message)


def validate_email(value, errors, field="email"):
    if not value or not EMAIL_RE.match(value.strip()):
        add_error(errors, field, "Enter a valid email address")
        return None
    return value.strip().lower()


def validate_password(value, errors, field="password"):
    if not value or not PASSWORD_RE.match(value):
        add_error(
            errors,
            field,
            "Password must be at least 8 characters and include a letter and a number",
        )
        return None
    return value


def validate_non_empty(value, errors, field, label=None):
    if value is None or str(value).strip() == "":
        add_error(errors, field, f"{label or field.title()} is required")
        return None
    return str(value).strip()


def validate_cgpa(value, errors, field="cgpa"):
    try:
        cgpa = float(value)
    except (TypeError, ValueError):
        add_error(errors, field, "CGPA must be a number")
        return None
    if not (0.0 <= cgpa <= 10.0):
        add_error(errors, field, "CGPA must be between 0 and 10")
        return None
    return cgpa


def validate_graduation_year(value, errors, field="graduation_year"):
    try:
        year = int(value)
    except (TypeError, ValueError):
        add_error(errors, field, "Graduation year must be a number")
        return None
    if not (CURRENT_YEAR <= year <= CURRENT_YEAR + 6):
        add_error(
            errors, field, f"Graduation year must be between {CURRENT_YEAR} and {CURRENT_YEAR + 6}"
        )
        return None
    return year


def validate_phone(value, errors, field="phone"):
    if value in (None, ""):
        return None  # optional field
    if not PHONE_RE.match(str(value).strip()):
        add_error(errors, field, "Phone number must be exactly 10 digits")
        return None
    return str(value).strip()


def validate_branch(value, errors, field="branch"):
    allowed = current_app.config["ALLOWED_BRANCHES"]
    if value not in allowed:
        add_error(errors, field, f"Branch must be one of: {', '.join(allowed)}")
        return None
    return value


def validate_branches_list(values, errors, field="eligible_branches"):
    allowed = set(current_app.config["ALLOWED_BRANCHES"])
    if not values:
        add_error(errors, field, "Select at least one eligible branch")
        return None
    cleaned = [v.strip() for v in values if v.strip()]
    invalid = [v for v in cleaned if v not in allowed]
    if invalid:
        add_error(errors, field, f"Invalid branch(es): {', '.join(invalid)}")
        return None
    return cleaned


def validate_years_list(values, errors, field="eligible_years"):
    if not values:
        add_error(errors, field, "Select at least one eligible graduation year")
        return None
    try:
        years = [int(v) for v in values]
    except (TypeError, ValueError):
        add_error(errors, field, "Eligible years must be numbers")
        return None
    for y in years:
        if not (CURRENT_YEAR - 1 <= y <= CURRENT_YEAR + 6):
            add_error(errors, field, "Eligible years out of allowed range")
            return None
    return years


def validate_deadline(value, errors, field="deadline"):
    if not value:
        add_error(errors, field, "Deadline is required")
        return None
    try:
        parsed = value if isinstance(value, date) else datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        add_error(errors, field, "Deadline must be a valid date (YYYY-MM-DD)")
        return None
    if parsed < date.today():
        add_error(errors, field, "Deadline cannot be in the past")
        return None
    return parsed


def validate_resume_file(file_storage, errors, field="resume"):
    if file_storage is None or file_storage.filename == "":
        add_error(errors, field, "Select a resume file")
        return None

    filename = file_storage.filename
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    allowed = current_app.config["ALLOWED_RESUME_EXTENSIONS"]
    if ext not in allowed:
        add_error(errors, field, f"Resume must be one of: {', '.join(sorted(allowed))}")
        return None

    file_storage.seek(0, 2)
    size = file_storage.tell()
    file_storage.seek(0)
    if size > current_app.config["MAX_CONTENT_LENGTH"]:
        add_error(errors, field, "Resume must be under 5 MB")
        return None

    mime = file_storage.mimetype or ""
    allowed_mimes = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    if mime not in allowed_mimes:
        add_error(errors, field, "Resume file type not recognized")
        return None

    return file_storage


def is_eligible(student_profile, drive):
    """Pure boolean eligibility check, reused outside request/error-collecting contexts (e.g. Celery tasks)."""
    return (
        student_profile.branch in drive.branches_list()
        and student_profile.cgpa >= drive.min_cgpa
        and student_profile.graduation_year in drive.years_list()
    )


def validate_eligibility(student_profile, drive, errors, field="eligibility"):
    if student_profile.branch not in drive.branches_list():
        add_error(errors, field, "You are not eligible for this drive (branch)")
        return False
    if student_profile.cgpa < drive.min_cgpa:
        add_error(errors, field, "You are not eligible for this drive (CGPA below minimum)")
        return False
    if student_profile.graduation_year not in drive.years_list():
        add_error(errors, field, "You are not eligible for this drive (graduation year)")
        return False
    return True


def validate_drive_open(drive, errors, field="drive"):
    if not drive.is_open():
        add_error(errors, field, "This drive is not open for applications")
        return False
    return True


def validate_no_duplicate_application(exists, errors, field="drive"):
    if exists:
        add_error(errors, field, "You have already applied to this drive")
        return False
    return True


def validate_status_transition(current_status, new_status, errors, field="status"):
    if new_status not in APPLICATION_TRANSITIONS.get(current_status, set()):
        add_error(
            errors,
            field,
            f"Cannot change status from '{current_status}' to '{new_status}'",
        )
        return False
    return True
