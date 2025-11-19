"""
ASGI config for AgentVerse Cloud Backend.

It exposes the ASGI callable as a module-level variable named ``application``.

This supports both HTTP and WebSocket connections.

WebSocket Security:
- JWT authentication for all WebSocket connections
- Token can be passed via query parameter (?token=<jwt>) or Authorization header
- Allowed hosts validation to prevent CSRF

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Import websocket routing and JWT middleware after Django app is initialized
from apps.messages.routing import websocket_urlpatterns
from apps.core.websocket_middleware import JWTAuthMiddlewareStack

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})
