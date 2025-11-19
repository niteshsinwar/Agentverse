"""
WebSocket URL routing for real-time features.

Endpoints:
- ws/messages/<group_id>/ - Real-time chat messages
- ws/sync/ - Cloud→Local config synchronization
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Real-time chat messages for a specific group
    re_path(r'ws/messages/(?P<group_id>[^/]+)/$', consumers.MessageConsumer.as_asgi()),

    # Cloud→Local synchronization channel
    re_path(r'ws/sync/$', consumers.CloudSyncConsumer.as_asgi()),
]
