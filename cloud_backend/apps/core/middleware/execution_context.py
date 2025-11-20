"""
Execution Context Middleware

Extracts execution context from request headers and attaches to request object.

Headers extracted:
- X-Device-ID: Device making the request (for WebSocket routing)
- X-Execution-ID: Unique execution chain ID
- X-Initiator-User-ID: User who initiated the execution chain
- X-Initiator-Device-ID: Device where execution started
- X-Call-Depth: Current depth in agent call chain

Author: AgentVerse Team
"""

import logging

logger = logging.getLogger(__name__)


class ExecutionContextMiddleware:
    """
    Extract execution context from request headers.

    This middleware captures:
    1. Device identification for WebSocket routing
    2. Execution chain metadata for analytics and debugging
    3. Initiator tracking for cost attribution

    The extracted context is attached to request.execution_context
    and can be used by views to:
    - Store execution metadata in database
    - Route WebSocket messages to specific devices
    - Track execution chains for analytics
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract device ID (CRITICAL for WebSocket routing)
        device_id = request.headers.get('X-Device-ID')

        # Extract execution context headers
        execution_id = request.headers.get('X-Execution-ID')
        initiator_user_id = request.headers.get('X-Initiator-User-ID')
        initiator_device_id = request.headers.get('X-Initiator-Device-ID')
        call_depth = request.headers.get('X-Call-Depth', '0')

        # Attach to request
        if execution_id:
            # Full execution context available
            request.execution_context = {
                'device_id': device_id,
                'execution_id': execution_id,
                'initiator_user_id': initiator_user_id,
                'initiator_device_id': initiator_device_id,
                'call_depth': int(call_depth) if call_depth.isdigit() else 0
            }

            logger.debug(
                f"Execution context: {execution_id[:8]}... "
                f"(initiator: {initiator_user_id[:8] if initiator_user_id else 'N/A'}..., "
                f"depth: {call_depth})"
            )
        elif device_id:
            # Only device ID available (non-agent request)
            request.execution_context = {
                'device_id': device_id,
                'execution_id': None,
                'initiator_user_id': None,
                'initiator_device_id': None,
                'call_depth': 0
            }

            logger.debug(f"Device ID: {device_id[:8]}...")
        else:
            # No execution context
            request.execution_context = None

        response = self.get_response(request)
        return response
