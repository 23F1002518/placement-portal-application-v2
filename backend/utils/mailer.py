import logging

from flask_mail import Message

from extensions import mail

logger = logging.getLogger(__name__)


def send_email(subject, recipients, html_body, attachments=None):
    """Send an email via the configured Gmail SMTP account.

    Never raises: a mail outage must not break the calling request or Celery task.
    `attachments` is an optional list of (filename, mimetype, data_bytes) tuples.
    """
    try:
        msg = Message(subject=subject, recipients=recipients, html=html_body)
        for filename, mimetype, data in attachments or []:
            msg.attach(filename, mimetype, data)
        mail.send(msg)
        return True
    except Exception:
        logger.exception("Failed to send email: subject=%r recipients=%r", subject, recipients)
        return False
