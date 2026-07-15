import os
from datetime import timedelta
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    # --- Core / DB ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'placement.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Initial admin (seeded automatically on db.create_all) ---
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@placementportal.local")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@123")

    # --- JWT ---
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_TOKEN_LOCATION = ["headers"]

    # --- Redis / Cache ---
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TYPE = os.environ.get("CACHE_TYPE", "RedisCache")
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300

    # --- Celery ---
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)

    # --- Mail (Gmail SMTP) ---
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True") == "True"
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "False") == "True"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", MAIL_USERNAME)
    MAIL_SUPPRESS_SEND = os.environ.get("MAIL_SUPPRESS_SEND", "False") == "True"

    # --- Uploads ---
    UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
    RESUME_DIR = os.path.join(UPLOAD_DIR, "resumes")
    EXPORT_DIR = os.path.join(UPLOAD_DIR, "exports")
    OFFER_LETTER_DIR = os.path.join(UPLOAD_DIR, "offer_letters")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
    ALLOWED_RESUME_EXTENSIONS = {"pdf", "doc", "docx"}

    # --- CORS ---
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

    # --- Batch job tuning ---
    REMINDER_HOUR = int(os.environ.get("REMINDER_HOUR", 8))
    REMINDER_WINDOW_DAYS = int(os.environ.get("REMINDER_WINDOW_DAYS", 3))

    # --- Domain enums ---
    ALLOWED_BRANCHES = [
        "Computer Science",
        "Information Technology",
        "Electronics",
        "Electrical",
        "Mechanical",
        "Civil",
        "Chemical",
        "Other",
    ]
