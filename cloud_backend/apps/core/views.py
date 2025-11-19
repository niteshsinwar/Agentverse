"""
Core Views - Health check and system status
"""

from django.http import JsonResponse
from django.conf import settings
from django.db import connection
import redis


def health_check(request):
    """
    Simple health check endpoint.

    Returns 200 if system is up.
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'agentverse-cloud',
        'version': '1.0.0',
    })


def system_status(request):
    """
    Detailed system status with service checks.

    Checks:
    - Database connection
    - Redis connection
    - Current tenant
    """
    status_data = {
        'database': 'unknown',
        'redis': 'unknown',
        'tenant': connection.schema_name if hasattr(connection, 'schema_name') else 'public',
    }

    # Check database
    try:
        connection.ensure_connection()
        status_data['database'] = 'connected'
    except Exception as e:
        status_data['database'] = f'error: {str(e)}'

    # Check Redis
    try:
        redis_client = redis.from_url(settings.CELERY_BROKER_URL)
        redis_client.ping()
        status_data['redis'] = 'connected'
    except Exception as e:
        status_data['redis'] = f'error: {str(e)}'

    return JsonResponse(status_data)
