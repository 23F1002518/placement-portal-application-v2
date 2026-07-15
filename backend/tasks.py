import csv
import io
import os
from datetime import date, timedelta, datetime
from collections import defaultdict

from flask import current_app

from extensions import celery, db
from models import StudentProfile, Drive, Application, User, CompanyProfile, ROLE_ADMIN
from utils.mailer import send_email
from utils.validators import is_eligible


@celery.task(name="tasks.daily_reminders")
def daily_reminders():
    """Remind students about drives closing soon: eligible-but-not-applied, and in-flight applications."""
    window_days = current_app.config["REMINDER_WINDOW_DAYS"]
    today = date.today()
    upper = today + timedelta(days=window_days)

    open_drives = Drive.query.filter(
        Drive.status == "Approved", Drive.deadline >= today, Drive.deadline <= upper
    ).all()
    if not open_drives:
        return {"reminders_sent": 0}

    sent = 0
    students = StudentProfile.query.join(User).filter(User.active.is_(True), User.blacklisted.is_(False)).all()

    for student in students:
        applied_drive_ids = {a.drive_id for a in student.applications}

        eligible_new = [
            d for d in open_drives if d.id not in applied_drive_ids and is_eligible(student, d)
        ]
        in_flight = [
            a for a in student.applications
            if a.status in ("Applied", "Shortlisted") and a.drive in open_drives
        ]

        if not eligible_new and not in_flight:
            continue

        rows = []
        for d in eligible_new:
            rows.append(f"<li><b>{d.title}</b> ({d.company.name}) — apply by {d.deadline.isoformat()}</li>")
        for a in in_flight:
            rows.append(
                f"<li>Your application to <b>{a.drive.title}</b> ({a.drive.company.name}) "
                f"closes on {a.drive.deadline.isoformat()} — status: {a.status}</li>"
            )

        html = f"""
        <h2>Upcoming placement deadlines</h2>
        <p>Hi {student.name},</p>
        <p>The following drives close within the next {window_days} day(s):</p>
        <ul>{''.join(rows)}</ul>
        <p>— Placement Portal</p>
        """
        if send_email("Placement drive deadline reminder", [student.user.email], html):
            sent += 1

    return {"reminders_sent": sent}


def _build_monthly_html(drives_count, applied_count, selected_count, period_label):
    return f"""
    <h2>Monthly Placement Activity Report — {period_label}</h2>
    <table border="1" cellpadding="8" cellspacing="0">
        <tr><td>Drives conducted</td><td>{drives_count}</td></tr>
        <tr><td>Students applied</td><td>{applied_count}</td></tr>
        <tr><td>Students selected</td><td>{selected_count}</td></tr>
    </table>
    <p>— Placement Portal (automated report)</p>
    """


def _build_monthly_pdf(drives_count, applied_count, selected_count, period_label):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, f"Monthly Placement Report — {period_label}")
    c.setFont("Helvetica", 12)
    lines = [
        f"Drives conducted: {drives_count}",
        f"Students applied: {applied_count}",
        f"Students selected: {selected_count}",
    ]
    y = height - 110
    for line in lines:
        c.drawString(72, y, line)
        y -= 20
    c.showPage()
    c.save()
    return buf.getvalue()


@celery.task(name="tasks.monthly_report")
def monthly_report():
    """Build the previous month's activity report and email it to the admin (HTML + PDF)."""
    today = date.today()
    first_of_this_month = today.replace(day=1)
    last_day_prev_month = first_of_this_month - timedelta(days=1)
    period_start = last_day_prev_month.replace(day=1)
    period_end = first_of_this_month
    period_label = period_start.strftime("%B %Y")

    drives_count = Drive.query.filter(
        Drive.created_at >= period_start, Drive.created_at < period_end
    ).count()
    applied_count = Application.query.filter(
        Application.applied_at >= period_start, Application.applied_at < period_end
    ).count()
    selected_count = Application.query.filter(
        Application.status == "Selected",
        Application.applied_at >= period_start,
        Application.applied_at < period_end,
    ).count()

    html = _build_monthly_html(drives_count, applied_count, selected_count, period_label)
    pdf_bytes = _build_monthly_pdf(drives_count, applied_count, selected_count, period_label)

    admin_user = User.query.filter_by(role=ROLE_ADMIN).first()
    if not admin_user:
        return {"sent": False, "reason": "no admin user found"}

    ok = send_email(
        f"Monthly Placement Report — {period_label}",
        [admin_user.email],
        html,
        attachments=[(f"report_{period_label.replace(' ', '_')}.pdf", "application/pdf", pdf_bytes)],
    )
    return {"sent": ok, "period": period_label}


@celery.task(name="tasks.notify_company_approved")
def notify_company_approved(company_user_id):
    """Email a company that the admin has approved its registration."""
    user = db.session.get(User, company_user_id)
    if not user or not user.company_profile:
        return {"sent": False, "reason": "company not found"}

    company = user.company_profile
    html = f"""
    <h2>Registration approved</h2>
    <p>Hi {company.name},</p>
    <p>Good news — your company registration on the Placement Portal has been
    <b>approved</b> by the admin. You can now log in and start posting placement drives.</p>
    <p>— Placement Portal</p>
    """
    ok = send_email(
        "Your Placement Portal registration has been approved",
        [user.email],
        html,
    )
    return {"sent": ok, "company": company.name}


@celery.task(name="tasks.notify_interview_scheduled")
def notify_interview_scheduled(application_id):
    """Email a student immediately when a company schedules/reschedules their interview."""
    application = db.session.get(Application, application_id)
    if not application or not application.interview_datetime:
        return {"sent": False, "reason": "application or interview time not found"}

    student = application.student
    when = application.interview_datetime.strftime("%A, %d %B %Y at %I:%M %p")
    html = f"""
    <h2>Interview scheduled</h2>
    <p>Hi {student.name},</p>
    <p><b>{application.drive.company.name}</b> has scheduled your interview for the role
    <b>{application.drive.title}</b>.</p>
    <p><b>Date &amp; time:</b> {when}</p>
    <p>Please be available on time. You can also see this on your student dashboard.</p>
    <p>— Placement Portal</p>
    """
    ok = send_email(
        f"Interview scheduled — {application.drive.title}",
        [student.user.email],
        html,
    )
    return {"sent": ok, "student": student.name, "when": when}


@celery.task(name="tasks.email_offer_letter")
def email_offer_letter(application_id):
    """Email the generated offer letter PDF to the student."""
    application = db.session.get(Application, application_id)
    if not application or not application.offer_letter:
        return {"sent": False, "reason": "offer letter not found"}

    student = application.student
    directory = current_app.config["OFFER_LETTER_DIR"]
    filename = os.path.basename(application.offer_letter.file_path)
    abs_path = os.path.join(directory, filename)
    try:
        with open(abs_path, "rb") as f:
            pdf_bytes = f.read()
    except OSError:
        return {"sent": False, "reason": "offer letter file missing"}

    company_name = application.drive.company.name
    html = f"""
    <h2>Congratulations — you have an offer!</h2>
    <p>Hi {student.name},</p>
    <p><b>{company_name}</b> has issued your offer letter for the role
    <b>{application.drive.title}</b>. Your offer letter is attached to this email as a PDF.</p>
    <p>— Placement Portal</p>
    """
    ok = send_email(
        f"Your offer letter — {company_name}",
        [student.user.email],
        html,
        attachments=[(filename, "application/pdf", pdf_bytes)],
    )
    return {"sent": ok, "student": student.name}


@celery.task(name="tasks.export_applications_csv", bind=True)
def export_applications_csv(self, student_user_id):
    """Generate a CSV of the student's application history and email a ready alert."""
    user = db.session.get(User, student_user_id)
    if not user or not user.student_profile:
        return {"ok": False, "reason": "student not found"}

    student = user.student_profile
    export_dir = current_app.config["EXPORT_DIR"]
    os.makedirs(export_dir, exist_ok=True)
    filename = f"export_user{student_user_id}_{self.request.id}.csv"
    abs_path = os.path.join(export_dir, filename)

    # Build the CSV once in memory so we can both persist it (dashboard download)
    # and attach the exact same bytes to the notification email.
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Student ID", "Company Name", "Drive Title", "Application Status", "Applied Date"])
    for application in student.applications:
        writer.writerow(
            [
                student.user_id,
                application.drive.company.name,
                application.drive.title,
                application.status,
                application.applied_at.strftime("%Y-%m-%d") if application.applied_at else "",
            ]
        )
    csv_text = buf.getvalue()

    with open(abs_path, "w", newline="", encoding="utf-8") as f:
        f.write(csv_text)

    rel_path = os.path.join("uploads", "exports", filename)
    send_email(
        "Your placement application export is ready",
        [user.email],
        f"<p>Hi {student.name},</p><p>Your CSV export is attached to this email. "
        f"You can also download it from your student dashboard.</p>",
        attachments=[(filename, "text/csv", csv_text.encode("utf-8"))],
    )

    return {"ok": True, "file": rel_path}
