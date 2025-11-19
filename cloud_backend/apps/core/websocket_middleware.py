"""
WebSocket Authentication Middleware

Provides JWT authentication for WebSocket connections.
Extracts token from query parameters or headers and validates it.
"""

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from urllib.parse import parse_qs
import jwt
import logging

logger = logging.getLogger(__name__)


@database_sync_to_async
def get_user_from_token(token):
    """
    Decode JWT token and return corresponding user.

    Args:
        token: JWT token string

    Returns:
        User instance or AnonymousUser
    """
    from apps.users.models import User

    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=['HS256']
        )

        # Extract user ID
        user_id = payload.get('user_id')
        if not user_id:
            logger.warning("JWT token missing user_id")
            return AnonymousUser()

        # Fetch user from database
        user = User.objects.get(id=user_id)

        if not user.is_active:
            logger.warning(f"User {user_id} is inactive")
            return AnonymousUser()

        return user

    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        return AnonymousUser()

    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return AnonymousUser()

    except User.DoesNotExist:
        logger.warning(f"User {user_id} not found")
        return AnonymousUser()

    except Exception as e:
        logger.error(f"Error decoding JWT token: {e}")
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware for JWT authentication in WebSocket connections.

    Extracts token from:
    1. Query parameter: ?token=<jwt>
    2. Header: Authorization: Bearer <jwt>
    """

    async def __call__(self, scope, receive, send):
        # Only process WebSocket connections
        if scope['type'] != 'websocket':
            return await super().__call__(scope, receive, send)

        # Try to extract token from query parameters
        token = None
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)

        if 'token' in query_params:
            token = query_params['token'][0]
        else:
            # Try to extract from headers (Authorization: Bearer <token>)
            headers = dict(scope.get('headers', []))
            auth_header = headers.get(b'authorization', b'').decode()

            if auth_header.startswith('Bearer '):
                token = auth_header[7:]  # Remove 'Bearer ' prefix

        # Authenticate user if token exists
        if token:
            scope['user'] = await get_user_from_token(token)
            logger.info(f"WebSocket authenticated user: {scope['user']}")
        else:
            scope['user'] = AnonymousUser()
            logger.debug("WebSocket connection without authentication token")

        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    """
    Convenience function to wrap ASGI application with JWT auth middleware.

    Usage:
        application = ProtocolTypeRouter({
            'websocket': JWTAuthMiddlewareStack(
                URLRouter(websocket_urlpatterns)
            ),
        })
    """
    return JWTAuthMiddleware(inner)
