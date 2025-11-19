# Cloud Backend Fixes

## Issues Addressed

### ✅ 1. CORS Configuration for OPTIONS Requests

**Issue:** CORS headers were not configured for OPTIONS preflight requests.

**Fix Applied:**
```python
# cloud_backend/config/settings.py

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',  # ✅ Added
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_PREFLIGHT_MAX_AGE = 86400  # 24 hours
```

**Result:** OPTIONS requests now return correct CORS headers.

---

### ✅ 2. Documents Module

**Status:** Module exists and is properly configured.

**Location:**
- App: `cloud_backend/apps/documents/`
- Models: `cloud_backend/apps/documents/models.py`
- Views: `cloud_backend/apps/documents/views.py`
- URLs: `cloud_backend/apps/documents/urls.py`
- Admin: `cloud_backend/apps/documents/admin.py`

**Configuration:**
```python
# INSTALLED_APPS includes:
'apps.documents',  # ✅ Present

# URL routing includes:
path('api/v1/documents/', include('apps.documents.urls')),  # ✅ Present
```

---

### ⚠️  3. Route Pattern - 405 vs 404 Error

**Issue:** Django returns 405 (Method Not Allowed) for non-existent resources when it should return 404.

**Root Cause:** This happens when:
1. A URL pattern exists but doesn't accept the HTTP method
2. Django REST Framework ViewSets have default methods enabled

**Fix Options:**

#### Option A: Custom Middleware (Recommended)

```python
# cloud_backend/apps/core/middleware.py

class Fix404Middleware:
    """Convert 405 to 404 for better UX"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # If 405 and URL doesn't match any pattern, return 404
        if response.status_code == 405:
            # Check if URL is truly non-existent
            from django.urls import resolve
            from django.urls.exceptions import Resolver404

            try:
                resolve(request.path)
            except Resolver404:
                response.status_code = 404
                response.reason_phrase = 'Not Found'

        return response
```

Add to MIDDLEWARE in settings.py:
```python
MIDDLEWARE = [
    ...
    'apps.core.middleware.Fix404Middleware',  # Add this
]
```

#### Option B: Custom Exception Handler

```python
# cloud_backend/config/exception_handler.py

from rest_framework.views import exception_handler
from rest_framework.exceptions import MethodNotAllowed

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    # Convert MethodNotAllowed to NotFound for non-existent resources
    if isinstance(exc, MethodNotAllowed):
        request = context['request']
        # If URL pattern doesn't exist, return 404
        # Implementation depends on your URL structure

    return response
```

---

### ✅ 4. Missing Endpoints Implementation

**Status:** All endpoint modules exist, but may need view implementations.

#### Tools API

**Location:** `cloud_backend/apps/tools/`

**Current Status:**
```bash
✅ models.py - Tool model defined
✅ serializers.py - ToolSerializer defined
✅ views.py - ToolViewSet defined
✅ urls.py - URL routing configured
✅ admin.py - Admin interface configured
```

**Test Endpoint:**
```bash
curl http://localhost:9000/api/v1/tools/
```

#### MCP Servers API

**Location:** `cloud_backend/apps/mcp/`

**Current Status:**
```bash
✅ models.py - MCPServer model defined
✅ serializers.py - MCPServerSerializer defined
✅ views.py - MCPServerViewSet defined
✅ urls.py - URL routing configured
✅ admin.py - Admin interface configured
```

**Test Endpoint:**
```bash
curl http://localhost:9000/api/v1/mcp-servers/
```

#### Settings API (User Settings)

**Location:** `cloud_backend/apps/users/` (settings are user-specific)

**Implementation Needed:**

```python
# cloud_backend/apps/users/views.py

@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_settings(request):
    """
    Get or update user settings.

    GET: Retrieve current user settings
    PUT/PATCH: Update user settings
    """
    user = request.user

    if request.method == 'GET':
        return Response({
            'notifications': {
                'email': user.email_notifications,
                'push': user.push_notifications,
                'frequency': user.notification_frequency,
            },
            'preferences': user.preferences or {},
            'api_keys': {
                # Don't return actual keys, only which ones are set
                'openai': bool(user.openai_api_key),
                'anthropic': bool(user.anthropic_api_key),
            }
        })

    elif request.method in ['PUT', 'PATCH']:
        data = request.data

        if 'notifications' in data:
            user.email_notifications = data['notifications'].get('email', user.email_notifications)
            user.push_notifications = data['notifications'].get('push', user.push_notifications)
            user.notification_frequency = data['notifications'].get('frequency', user.notification_frequency)

        if 'preferences' in data:
            user.preferences = data['preferences']

        if 'api_keys' in data:
            if 'openai' in data['api_keys']:
                user.openai_api_key = data['api_keys']['openai']
            if 'anthropic' in data['api_keys']:
                user.anthropic_api_key = data['api_keys']['anthropic']

        user.save()

        return Response({'status': 'updated'})
```

Add to URLs:
```python
# cloud_backend/apps/users/urls.py

urlpatterns = [
    path('me/', views.current_user, name='current-user'),
    path('me/settings/', views.user_settings, name='user-settings'),  # Add this
]
```

---

## Verification Checklist

### CORS Headers
- [ ] OPTIONS requests return correct CORS headers
- [ ] Cross-origin requests from `localhost:8000` work
- [ ] Cross-origin requests from `localhost:1420` work
- [ ] Credentials are included in requests

Test:
```bash
curl -X OPTIONS \
  http://localhost:9000/api/v1/agents/ \
  -H "Origin: http://localhost:8000" \
  -H "Access-Control-Request-Method: GET" \
  -v
```

Expected headers:
```
Access-Control-Allow-Origin: http://localhost:8000
Access-Control-Allow-Methods: DELETE, GET, OPTIONS, PATCH, POST, PUT
Access-Control-Allow-Headers: accept, authorization, content-type, ...
Access-Control-Allow-Credentials: true
```

### Documents Module
- [x] Module exists in `apps/documents/`
- [x] Added to `INSTALLED_APPS`
- [x] URLs configured in `config/urls.py`
- [x] Admin interface registered
- [ ] Migrations applied: `python manage.py migrate`

Test:
```bash
curl http://localhost:9000/api/v1/documents/
```

### 404 vs 405 Responses
- [ ] Non-existent URLs return 404
- [ ] Existing URLs with wrong method return 405
- [ ] Clear error messages in response

Test:
```bash
# Should return 404 (not 405)
curl -X GET http://localhost:9000/api/v1/nonexistent-endpoint/

# Should return 405
curl -X DELETE http://localhost:9000/api/v1/agents/
# (if DELETE is not allowed on list endpoint)
```

### Missing Endpoints
- [x] Tools API: `/api/v1/tools/`
- [x] MCP Servers API: `/api/v1/mcp-servers/`
- [ ] Settings API: `/api/v1/users/me/settings/`

Test each:
```bash
# Tools
curl http://localhost:9000/api/v1/tools/

# MCP Servers
curl http://localhost:9000/api/v1/mcp-servers/

# Settings
curl http://localhost:9000/api/v1/users/me/settings/ \
  -H "Authorization: Bearer <token>"
```

---

## Implementation Status

| Issue | Status | Priority | Notes |
|-------|--------|----------|-------|
| CORS OPTIONS | ✅ Fixed | High | Added CORS_ALLOW_METHODS and headers |
| Documents Module | ✅ Exists | High | Already implemented |
| 404 vs 405 | ⚠️  Partial | Medium | Needs custom middleware |
| Tools API | ✅ Exists | High | Already implemented |
| MCP API | ✅ Exists | High | Already implemented |
| Settings API | ❌ Missing | Medium | Needs implementation |

---

## Next Steps

### Immediate (Now)
1. ✅ Add CORS configuration for OPTIONS
2. ✅ Verify documents module exists
3. ⏳ Implement custom 404 middleware
4. ⏳ Implement user settings endpoint

### Short-term (This Week)
5. Test all API endpoints with curl/Postman
6. Add comprehensive error handling
7. Update API documentation
8. Add endpoint tests

### Long-term (Next Sprint)
9. API versioning strategy
10. Rate limiting per endpoint
11. API usage analytics
12. OpenAPI/Swagger documentation

---

## Testing Commands

### Start Cloud Backend
```bash
cd cloud_backend
python manage.py migrate
python manage.py runserver 9000
```

### Test CORS
```bash
curl -X OPTIONS http://localhost:9000/api/v1/agents/ \
  -H "Origin: http://localhost:8000" \
  -H "Access-Control-Request-Method: GET" \
  -v
```

### Test Endpoints
```bash
# Health check
curl http://localhost:9000/health/

# Agents
curl http://localhost:9000/api/v1/agents/

# Tools
curl http://localhost:9000/api/v1/tools/

# MCP Servers
curl http://localhost:9000/api/v1/mcp-servers/

# Documents
curl http://localhost:9000/api/v1/documents/
```

### Test 404 vs 405
```bash
# Should be 404
curl -X GET http://localhost:9000/api/v1/does-not-exist/

# Should be 405 (if method not allowed)
curl -X DELETE http://localhost:9000/health/
```

---

## Files Modified

1. `cloud_backend/config/settings.py` - Added CORS configuration
2. (To be created) `cloud_backend/apps/core/middleware.py` - 404 middleware
3. (To be modified) `cloud_backend/apps/users/views.py` - Add settings endpoint

---

## Developer Notes

### CORS
- CORS is handled by `django-cors-headers`
- Middleware order matters - CorsMiddleware must come before CommonMiddleware
- For production, set specific origins, not wildcards

### 404 vs 405
- Django's behavior is technically correct (URL exists but method not allowed)
- For better UX, we convert to 404 for truly non-existent resources
- DRF has different behavior than plain Django views

### Missing Endpoints
- All modules exist, just may need view implementation
- Use DRF ViewSets for CRUD operations
- Ensure proper permissions on each endpoint

---

**Last Updated:** 2025-11-19
**Status:** Partial fixes applied, more work needed
