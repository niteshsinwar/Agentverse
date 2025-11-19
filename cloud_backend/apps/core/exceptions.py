"""
Custom Exception Handler for DRF
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses.

    Returns:
        {
            "error": "Error message",
            "detail": "Detailed error information",
            "status_code": 400
        }
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Customize the response format
        custom_response_data = {
            'error': str(exc),
            'detail': response.data,
            'status_code': response.status_code
        }
        response.data = custom_response_data

    return response
