from alx_backend_graphql.settings import *  # noqa: F401,F403

# django-crontab
if "django_crontab" not in INSTALLED_APPS:
    INSTALLED_APPS = list(INSTALLED_APPS) + ["django_crontab"]

# django-celery-beat
if "django_celery_beat" not in INSTALLED_APPS:
    INSTALLED_APPS = list(INSTALLED_APPS) + ["django_celery_beat"]

CRONJOBS = [
    ('*/5 * * * *', 'crm.cron.log_crm_heartbeat'),
    ('0 */12 * * *', 'crm.cron.update_low_stock'),
]

# Celery + Redis broker
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

from celery.schedules import crontab  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    'generate-crm-report': {
        'task': 'crm.tasks.generate_crm_report',
        'schedule': crontab(day_of_week='mon', hour=6, minute=0),
    },
}
