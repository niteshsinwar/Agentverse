from celery import shared_task
from django.utils import timezone
from datetime import timedelta

@shared_task
def generate_usage_analytics():
    """Generate usage analytics for all tenants"""
    # TODO: Implement analytics aggregation
    print("Generating usage analytics...")
    return "Analytics generated"

@shared_task
def send_weekly_usage_reports():
    """Send weekly usage reports to tenant admins"""
    # TODO: Implement email reports
    print("Sending weekly usage reports...")
    return "Reports sent"

@shared_task
def cleanup_old_logs():
    """Cleanup logs older than 90 days"""
    from .models import UsageLog
    ninety_days_ago = timezone.now() - timedelta(days=90)
    deleted_count = UsageLog.objects.filter(created_at__lt=ninety_days_ago).delete()[0]
    return f"Deleted {deleted_count} old logs"
