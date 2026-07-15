"""Celery entry point. Run with:
    celery -A celery_app.celery worker --loglevel=info
    celery -A celery_app.celery beat --loglevel=info
"""
from celery.schedules import crontab

from app import create_app
from extensions import celery

flask_app = create_app()


def _init_celery(app):
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        # Windows has no fork(), so Celery's default 'prefork' pool crashes with
        # PermissionError(13, 'Access is denied') from billiard. Default to the
        # single-process 'solo' pool; override with --pool= on other platforms.
        worker_pool="solo",
        # Silence the Celery 6.0 CPendingDeprecationWarning about startup retries.
        broker_connection_retry_on_startup=True,
    )
    celery.conf.beat_schedule = {
        "daily-reminders": {
            "task": "tasks.daily_reminders",
            "schedule": crontab(hour=app.config["REMINDER_HOUR"], minute=0),
        },
        "monthly-report": {
            "task": "tasks.monthly_report",
            "schedule": crontab(day_of_month=1, hour=6, minute=0),
        },
    }

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


_init_celery(flask_app)

# Import after celery is configured so tasks register against this instance.
import tasks  # noqa: E402,F401
