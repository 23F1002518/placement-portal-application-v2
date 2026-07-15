from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

ROLE_ADMIN = "admin"
ROLE_COMPANY = "company"
ROLE_STUDENT = "student"

DRIVE_STATUSES = ["Pending", "Approved", "Rejected", "Closed"]
APPLICATION_STATUSES = ["Applied", "Shortlisted", "Selected", "Rejected"]

# Allowed forward transitions for an application's status.
APPLICATION_TRANSITIONS = {
    "Applied": {"Shortlisted", "Rejected"},
    "Shortlisted": {"Selected", "Rejected"},
    "Selected": set(),
    "Rejected": set(),
}


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin | company | student
    active = db.Column(db.Boolean, default=True, nullable=False)
    blacklisted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student_profile = db.relationship(
        "StudentProfile", backref="user", uselist=False, cascade="all, delete-orphan"
    )
    company_profile = db.relationship(
        "CompanyProfile", backref="user", uselist=False, cascade="all, delete-orphan"
    )

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def to_dict(self):
        data = {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "active": self.active,
            "blacklisted": self.blacklisted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if self.role == ROLE_STUDENT and self.student_profile:
            data["profile"] = self.student_profile.to_dict()
        elif self.role == ROLE_COMPANY and self.company_profile:
            data["profile"] = self.company_profile.to_dict()
        return data


class StudentProfile(db.Model):
    __tablename__ = "student_profile"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    branch = db.Column(db.String(60), nullable=False)
    cgpa = db.Column(db.Float, nullable=False)
    graduation_year = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    resume_path = db.Column(db.String(255), nullable=True)

    applications = db.relationship(
        "Application", backref="student", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "name": self.name,
            "branch": self.branch,
            "cgpa": self.cgpa,
            "graduation_year": self.graduation_year,
            "phone": self.phone,
            "resume_path": self.resume_path,
        }


class CompanyProfile(db.Model):
    __tablename__ = "company_profile"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    hr_contact = db.Column(db.String(120), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    approved = db.Column(db.Boolean, default=False, nullable=False)

    drives = db.relationship("Drive", backref="company", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "name": self.name,
            "hr_contact": self.hr_contact,
            "website": self.website,
            "description": self.description,
            "approved": self.approved,
        }


class Drive(db.Model):
    __tablename__ = "drive"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company_profile.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)

    eligible_branches = db.Column(db.String(255), nullable=False)  # comma-separated
    min_cgpa = db.Column(db.Float, nullable=False, default=0.0)
    eligible_years = db.Column(db.String(100), nullable=False)  # comma-separated ints

    deadline = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default="Pending", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship(
        "Application", backref="drive", cascade="all, delete-orphan"
    )

    def branches_list(self):
        return [b.strip() for b in self.eligible_branches.split(",") if b.strip()]

    def years_list(self):
        return [int(y) for y in self.eligible_years.split(",") if y.strip()]

    def is_open(self):
        return self.status == "Approved" and self.deadline >= date.today()

    def to_dict(self, applicant_count=None):
        data = {
            "id": self.id,
            "company_id": self.company_id,
            "company_name": self.company.name if self.company else None,
            "title": self.title,
            "description": self.description,
            "eligible_branches": self.branches_list(),
            "min_cgpa": self.min_cgpa,
            "eligible_years": self.years_list(),
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if applicant_count is not None:
            data["applicant_count"] = applicant_count
        return data


class Application(db.Model):
    __tablename__ = "application"
    __table_args__ = (
        db.UniqueConstraint("student_id", "drive_id", name="uq_student_drive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profile.id"), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey("drive.id"), nullable=False)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="Applied", nullable=False)
    interview_datetime = db.Column(db.DateTime, nullable=True)
    remarks = db.Column(db.Text, nullable=True)

    offer_letter = db.relationship(
        "OfferLetter", backref="application", uselist=False, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_user_id": self.student.user_id if self.student else None,
            "student_name": self.student.name if self.student else None,
            "drive_id": self.drive_id,
            "drive_title": self.drive.title if self.drive else None,
            "company_name": self.drive.company.name if self.drive and self.drive.company else None,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "status": self.status,
            "interview_datetime": self.interview_datetime.isoformat() if self.interview_datetime else None,
            "remarks": self.remarks,
            "has_offer_letter": self.offer_letter is not None,
        }


class OfferLetter(db.Model):
    __tablename__ = "offer_letter"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(
        db.Integer, db.ForeignKey("application.id"), unique=True, nullable=False
    )
    file_path = db.Column(db.String(255), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "application_id": self.application_id,
            "file_path": self.file_path,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
        }
