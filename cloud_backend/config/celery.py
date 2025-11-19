"""
Celery Configuration for AgentVerse Cloud Backend

Background tasks:
- Document processing
- Email notifications
- Usage analytics
- Backup operations
- Cache cleanup
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('agentverse_cloud')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Periodic tasks
app.conf.beat_schedule = {
    # Cleanup expired sessions every day at 3 AM
    'cleanup-expired-sessions': {
        'task': 'apps.core.tasks.cleanup_expired_sessions',
        'schedule': crontab(hour=3, minute=0),
    },

    # Generate usage analytics every hour
    'generate-usage-analytics': {
        'task': 'apps.analytics.tasks.generate_usage_analytics',
        'schedule': crontab(minute=0),
    },

    # Send usage reports every Monday at 9 AM
    'send-weekly-usage-reports': {
        'task': 'apps.analytics.tasks.send_weekly_usage_reports',
        'schedule': crontab(day_of_week=1, hour=9, minute=0),
    },

    # Cleanup old messages (older than 90 days) every Sunday at 2 AM
    'cleanup-old-messages': {
        'task': 'apps.messages.tasks.cleanup_old_messages',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),
    },

    # Check tenant storage limits every 6 hours
    'check-storage-limits': {
        'task': 'apps.tenants.tasks.check_storage_limits',
        'schedule': crontab(minute=0, hour='*/6'),
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to test Celery setup"""
    print(f'Request: {self.request!r}')
