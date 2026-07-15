"""Seed the database. Always creates the single admin. Pass --demo to also seed sample
companies/students/drives/applications for exercising dashboards, charts, and reports.

Usage:
    python create_initial_data.py
    python create_initial_data.py --demo
"""
import sys
from datetime import date, timedelta

from app import create_app, ensure_admin
from extensions import db
from models import (
    User,
    StudentProfile,
    CompanyProfile,
    Drive,
    Application,
    ROLE_COMPANY,
    ROLE_STUDENT,
)


def seed_admin(app):
    # The app factory already seeds the admin on db.create_all(); this call is
    # idempotent and just reports what happened when run standalone.
    if ensure_admin():
        print(
            f"Seeded admin: {app.config['ADMIN_EMAIL']} / {app.config['ADMIN_PASSWORD']}"
        )
    else:
        print("Admin already exists — skipping.")


def seed_demo_data():
    if CompanyProfile.query.first() or StudentProfile.query.first():
        print("Demo data already present — skipping.")
        return

    companies_spec = [
        ("techcorp@example.com", "TechCorp", "Priya HR", "https://techcorp.example.com", True),
        ("innosoft@example.com", "InnoSoft", "Rahul HR", "https://innosoft.example.com", True),
        ("newstartup@example.com", "NewStartup", "Asha HR", "https://newstartup.example.com", False),
    ]
    companies = []
    for email, name, hr, site, approved in companies_spec:
        user = User(email=email, role=ROLE_COMPANY)
        user.set_password("Company@123")
        user.company_profile = CompanyProfile(
            name=name, hr_contact=hr, website=site, approved=approved
        )
        db.session.add(user)
        companies.append(user)
    db.session.flush()

    students_spec = [
        ("alice@example.com", "Alice", "Computer Science", 8.9, date.today().year, "9000000001"),
        ("bob@example.com", "Bob", "Electronics", 7.2, date.today().year, "9000000002"),
        ("carol@example.com", "Carol", "Mechanical", 6.5, date.today().year + 1, "9000000003"),
        ("dave@example.com", "Dave", "Computer Science", 9.4, date.today().year, "9000000004"),
        ("eve@example.com", "Eve", "Civil", 7.8, date.today().year + 1, "9000000005"),
        ("frank@example.com", "Frank", "Information Technology", 6.9, date.today().year, "9000000006"),
        ("grace@example.com", "Grace", "Electrical", 8.1, date.today().year + 1, "9000000007"),
        ("heidi@example.com", "Heidi", "Chemical", 7.0, date.today().year, "9000000008"),
    ]
    students = []
    for email, name, branch, cgpa, grad_year, phone in students_spec:
        user = User(email=email, role=ROLE_STUDENT)
        user.set_password("Student@123")
        user.student_profile = StudentProfile(
            name=name, branch=branch, cgpa=cgpa, graduation_year=grad_year, phone=phone
        )
        db.session.add(user)
        students.append(user)
    db.session.flush()

    approved_companies = [c for c in companies if c.company_profile.approved]

    drives_spec = [
        ("Software Engineer", "Computer Science,Information Technology", 6.0, [date.today().year], 20, "Approved"),
        ("Hardware Design Intern", "Electronics,Electrical", 6.5, [date.today().year, date.today().year + 1], 10, "Approved"),
        ("Site Engineer", "Civil,Mechanical", 6.0, [date.today().year + 1], 15, "Pending"),
        ("Data Analyst", "Computer Science,Information Technology,Electrical", 7.0, [date.today().year], 5, "Approved"),
        ("Process Engineer", "Chemical,Mechanical", 6.5, [date.today().year], 2, "Closed"),
    ]
    drives = []
    for i, (title, branches, min_cgpa, years, days_ahead, status) in enumerate(drives_spec):
        company = approved_companies[i % len(approved_companies)]
        drive = Drive(
            company_id=company.company_profile.id,
            title=title,
            description=f"{title} role — demo drive.",
            eligible_branches=branches,
            min_cgpa=min_cgpa,
            eligible_years=",".join(str(y) for y in years),
            deadline=date.today() + timedelta(days=days_ahead),
            status=status,
        )
        db.session.add(drive)
        drives.append(drive)
    db.session.flush()

    application_statuses = ["Applied", "Shortlisted", "Selected", "Rejected"]
    pairs = [
        (students[0], drives[0], "Selected"),
        (students[1], drives[1], "Shortlisted"),
        (students[3], drives[0], "Applied"),
        (students[3], drives[3], "Shortlisted"),
        (students[6], drives[1], "Rejected"),
        (students[2], drives[2], "Applied"),
    ]
    for student, drive, status in pairs:
        db.session.add(
            Application(student_id=student.student_profile.id, drive_id=drive.id, status=status)
        )

    db.session.commit()
    print(f"Seeded {len(companies)} companies, {len(students)} students, {len(drives)} drives, {len(pairs)} applications.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        seed_admin(app)
        if "--demo" in sys.argv:
            seed_demo_data()
