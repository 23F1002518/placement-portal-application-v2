import os
from datetime import datetime

from flask import current_app
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


def generate_offer_letter_pdf(application):
    """Render a dummy offer letter PDF for a Selected application. Returns the relative file path."""
    student = application.student
    drive = application.drive
    company = drive.company

    out_dir = current_app.config["OFFER_LETTER_DIR"]
    os.makedirs(out_dir, exist_ok=True)
    filename = f"offer_letter_app{application.id}.pdf"
    abs_path = os.path.join(out_dir, filename)

    c = canvas.Canvas(abs_path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 1.2 * inch, "Offer of Employment")

    c.setFont("Helvetica", 11)
    today = datetime.utcnow().strftime("%d %B %Y")
    lines = [
        "",
        f"Date: {today}",
        "",
        f"Dear {student.name},",
        "",
        f"On behalf of {company.name}, we are pleased to offer you the position of",
        f'"{drive.title}", following your successful participation in our placement drive.',
        "",
        "This offer is issued as part of a campus placement demonstration and is",
        "not a legally binding employment contract.",
        "",
        "We look forward to welcoming you to the team.",
        "",
        "Congratulations!",
        "",
        f"HR, {company.name}",
    ]

    text = c.beginText(1 * inch, height - 2 * inch)
    text.setFont("Helvetica", 11)
    text.setLeading(16)
    for line in lines:
        text.textLine(line)
    c.drawText(text)
    c.showPage()
    c.save()

    return os.path.join("uploads", "offer_letters", filename)
