from alx_backend_graphql.settings import *  # noqa: F401,F403

# Ensure django-crontab is installed
if "django_crontab" not in INSTALLED_APPS:
    INSTALLED_APPS = list(INSTALLED_APPS) + ["django_crontab"]

CRONJOBS = [
    ('*/5 * * * *', 'crm.cron.log_crm_heartbeat'),
    ('0 */12 * * *', 'crm.cron.update_low_stock'),
]
