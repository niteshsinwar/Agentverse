# AgentVerse - Complete Setup & Testing Guide

**Date:** 2025-11-20
**Purpose:** Step-by-step guide to install, configure, run, and test all three codebases

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Cloud Backend Setup](#cloud-backend-setup)
3. [Local Backend Setup](#local-backend-setup)
4. [Local Frontend Setup](#local-frontend-setup)
5. [Testing Data Flow](#testing-data-flow)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

```bash
# Check versions
python --version    # Python 3.10+
node --version      # Node 18+
npm --version       # npm 9+
psql --version      # PostgreSQL 14+
redis-cli --version # Redis 7+
```

### Installation (Ubuntu/Debian)

```bash
# Python 3.10+
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip

# PostgreSQL
sudo apt install postgresql postgresql-contrib

# Redis
sudo apt install redis-server

# Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### Installation (macOS)

```bash
# Using Homebrew
brew install python@3.10
brew install postgresql@14
brew install redis
brew install node@18
```

---

## Cloud Backend Setup

### Step 1: Navigate to Cloud Backend

```bash
cd /home/user/Agentverse/cloud_backend
```

### Step 2: Create Virtual Environment

```bash
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**If requirements.txt doesn't exist, install manually:**

```bash
pip install django==4.2
pip install djangorestframework==3.14
pip install django-tenants==3.5
pip install psycopg2-binary==2.9
pip install django-cors-headers==4.3
pip install djangorestframework-simplejwt==5.3
pip install channels==4.0
pip install channels-redis==4.1
pip install redis==5.0
pip install django-filter==23.3
pip install celery==5.3
pip install python-dotenv==1.0
pip install daphne==4.0
```

### Step 4: PostgreSQL Database Setup

```bash
# Start PostgreSQL service
sudo service postgresql start  # Linux
brew services start postgresql # macOS

# Create database and user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE agentverse_db;
CREATE USER agentverse_user WITH PASSWORD 'secure_password_123';
ALTER ROLE agentverse_user SET client_encoding TO 'utf8';
ALTER ROLE agentverse_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE agentverse_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE agentverse_db TO agentverse_user;

# Enable pgvector extension (for RAG)
\c agentverse_db
CREATE EXTENSION IF NOT EXISTS vector;

\q  # Exit PostgreSQL shell
```

### Step 5: Redis Setup

```bash
# Start Redis service
sudo service redis-server start  # Linux
brew services start redis        # macOS

# Test Redis connection
redis-cli ping  # Should return PONG
```

### Step 6: Environment Configuration

Create `.env` file in `cloud_backend/`:

```bash
cat > .env << 'EOF'
# Django Settings
SECRET_KEY=your-super-secret-key-change-this-in-production-min-50-chars
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,*.agentverse.com

# Database
DATABASE_NAME=agentverse_db
DATABASE_USER=agentverse_user
DATABASE_PASSWORD=secure_password_123
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# JWT
JWT_SECRET_KEY=your-jwt-secret-key-change-this
ACCESS_TOKEN_LIFETIME_MINUTES=60
REFRESH_TOKEN_LIFETIME_DAYS=7

# License Tiers
LICENSE_TIER_FREE_MAX_USERS=10
LICENSE_TIER_FREE_MAX_AGENTS=5
LICENSE_TIER_FREE_MAX_STORAGE_MB=1000

# Email (optional for notifications)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Celery (for background tasks)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
EOF
```

### Step 7: Update Django Settings

Ensure `cloud_backend/config/settings.py` uses environment variables:

```python
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST', 'localhost'),
        'PORT': os.getenv('DATABASE_PORT', '5432'),
    }
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(os.getenv('REDIS_HOST', 'localhost'), int(os.getenv('REDIS_PORT', 6379)))],
        },
    },
}
```

### Step 8: Run Migrations

```bash
# Create migrations for new models
python manage.py makemigrations

# Apply migrations to public schema
python manage.py migrate_schemas --shared

# Create initial tenant migrations (if not exists)
python manage.py migrate_schemas
```

### Step 9: Create Superuser

```bash
python manage.py createsuperuser
# Email: superadmin@agentverse.com
# Password: SuperAdminPass123!
```

### Step 10: Create Initial Tenants (via Python shell)

```bash
python manage.py shell
```

```python
from apps.tenants.models import Tenant, Domain, TenantMembership
from apps.users.models import User
from django.contrib.auth.hashers import make_password

# Create Tenant 1: Acme Corp
acme = Tenant.objects.create(
    schema_name='tenant_acme',
    name='Acme Corporation',
    slug='acme',
    email='admin@acme.com',
    admin_name='John Doe',
    license_type='pro',
    is_active=True
)

Domain.objects.create(
    domain='acme.localhost',
    tenant=acme,
    is_primary=True
)

# Switch to Acme schema and create admin user
from django.db import connection
connection.set_tenant(acme)

acme_admin = User.objects.create(
    email='john@acme.com',
    name='John Doe',
    password=make_password('AcmeAdmin123!'),
    role='admin',
    is_active=True
)

# Create TenantMembership
connection.set_schema_to_public()
TenantMembership.objects.create(
    tenant=acme,
    user=acme_admin,
    role='admin',
    is_active=True
)

# Create Tenant 2: Bharat Tech
bharat = Tenant.objects.create(
    schema_name='tenant_bharat',
    name='Bharat Tech Pvt Ltd',
    slug='bharat',
    email='admin@bharattech.com',
    admin_name='Priya Sharma',
    license_type='enterprise',
    is_active=True
)

Domain.objects.create(
    domain='bharat.localhost',
    tenant=bharat,
    is_primary=True
)

# Switch to Bharat schema
connection.set_tenant(bharat)

bharat_admin = User.objects.create(
    email='priya@bharattech.com',
    name='Priya Sharma',
    password=make_password('BharatAdmin123!'),
    role='admin',
    is_active=True
)

# Create TenantMembership
connection.set_schema_to_public()
TenantMembership.objects.create(
    tenant=bharat,
    user=bharat_admin,
    role='admin',
    is_active=True
)

print("✅ Tenants created successfully!")
print("Acme Corp: john@acme.com / AcmeAdmin123!")
print("Bharat Tech: priya@bharattech.com / BharatAdmin123!")
exit()
```

### Step 11: Run Cloud Backend

```bash
# Run with Daphne (ASGI server for WebSockets)
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Or with Django development server (HTTP only, no WebSocket in dev)
python manage.py runserver 0.0.0.0:8000
```

**Test:** Visit `http://localhost:8000/admin/` and login with superuser credentials.

---

## Local Backend Setup

### Step 1: Navigate to Local Backend

```bash
cd /home/user/Agentverse/local_backend
```

### Step 2: Create Virtual Environment

```bash
python3.10 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**If requirements.txt doesn't exist:**

```bash
pip install fastapi==0.104
pip install uvicorn[standard]==0.24
pip install pydantic==2.5
pip install pydantic-settings==2.1
pip install python-dotenv==1.0
pip install sqlalchemy==2.0
pip install websockets==12.0
pip install httpx==0.25
pip install python-multipart==0.0.6
```

### Step 4: Environment Configuration

Create `.env` file in `local_backend/`:

```bash
cat > .env << 'EOF'
# ---- Security (REQUIRED) ----
SECRET_KEY=z_E-0cQjGhkq5r9n9p6BzJXHCnlEBay8XUpJb17HTyQ

# ---- Cloud Backend Connection ----
CLOUD_BACKEND_URL=http://localhost:8000
CLOUD_WEBSOCKET_URL=ws://localhost:8000

# ---- LLM Keys ----
OPENAI_API_KEY=sk-your-openai-api-key
VLLM_ENDPOINT=http://localhost:8001/v1

# ---- Storage ----
EMBEDDINGS_MODEL=text-embedding-3-large
DATABASE_URL=sqlite:///./agentic.db

# ---- Server ----
HOST=0.0.0.0
PORT=8001
EOF
```

### Step 5: Initialize Database

```bash
# The local backend auto-initializes SQLite on first run
# No manual migration needed
```

### Step 6: Run Local Backend

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
```

**Test:** Visit `http://localhost:8001/docs` for API documentation.

---

## Local Frontend Setup

### Step 1: Navigate to Local Frontend

```bash
cd /home/user/Agentverse/local_frontend
```

### Step 2: Install Dependencies

```bash
npm install
```

**If package.json is missing key dependencies, install manually:**

```bash
npm install react@18
npm install react-dom@18
npm install react-router-dom@6
npm install zustand@4
npm install axios@1.6
npm install @heroicons/react@2.1
npm install react-hot-toast@2.4
npm install tailwindcss@3.4
npm install vite@5
```

### Step 3: Environment Configuration

Create `.env` file in `local_frontend/`:

```bash
cat > .env << 'EOF'
# Cloud Backend API
VITE_CLOUD_API_URL=http://localhost:8000/api/v1

# Local Backend API
VITE_LOCAL_API_URL=http://localhost:8001/api

# WebSocket URLs
VITE_CLOUD_WS_URL=ws://localhost:8000/ws
VITE_LOCAL_WS_URL=ws://localhost:8001/ws

# App Configuration
VITE_APP_NAME=AgentVerse
VITE_APP_VERSION=1.0.0
EOF
```

### Step 4: Update API Configuration

Ensure `local_frontend/src/lib/config.ts` uses env variables:

```typescript
export const env = {
  CLOUD_API_URL: import.meta.env.VITE_CLOUD_API_URL || 'http://localhost:8000/api/v1',
  LOCAL_API_URL: import.meta.env.VITE_LOCAL_API_URL || 'http://localhost:8001/api',
  CLOUD_WS_URL: import.meta.env.VITE_CLOUD_WS_URL || 'ws://localhost:8000/ws',
  LOCAL_WS_URL: import.meta.env.VITE_LOCAL_WS_URL || 'ws://localhost:8001/ws',
};
```

### Step 5: Run Local Frontend

```bash
npm run dev
```

**Test:** Visit `http://localhost:5173` in browser.

---

## Testing Data Flow

### Test 1: Authentication (3-Field Login)

**Test Case:** User logs in with tenant_id, email, password

```bash
# Using curl
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "acme",
    "email": "john@acme.com",
    "password": "AcmeAdmin123!"
  }'
```

**Expected Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "uuid",
    "email": "john@acme.com",
    "name": "John Doe",
    "role": "admin"
  },
  "tenant": {
    "id": "uuid",
    "name": "Acme Corporation",
    "slug": "acme"
  }
}
```

**UI Test:**
1. Open `http://localhost:5173`
2. Enter:
   - Tenant ID: `acme`
   - Email: `john@acme.com`
   - Password: `AcmeAdmin123!`
3. Click Login
4. Should redirect to dashboard

---

### Test 2: Create Agent (Tenant-Scoped)

**Test Case:** Tenant admin creates an agent

```bash
# Get JWT from login response
export JWT_TOKEN="your-jwt-token-here"

curl -X POST http://localhost:8000/api/v1/agents/ \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customer Support Bot",
    "description": "Handles customer inquiries",
    "emoji": "🤖",
    "llm_provider": "openai",
    "llm_model": "gpt-4",
    "system_prompt": "You are a helpful customer support assistant."
  }'
```

**Expected Response:**
```json
{
  "id": "uuid",
  "tenant": "uuid",
  "name": "Customer Support Bot",
  "description": "Handles customer inquiries",
  "emoji": "🤖",
  "llm_provider": "openai",
  "llm_model": "gpt-4",
  "created_at": "2025-11-20T10:00:00Z"
}
```

**Real-Time Sync Test:**
1. Open two browser windows
2. Login as `john@acme.com` in both
3. In window 1, create an agent via UI
4. Window 2 should receive `agent_updated` WebSocket event
5. Window 2 should show new agent without refresh

---

### Test 3: Create Group (Tenant-Scoped)

```bash
curl -X POST http://localhost:8000/api/v1/groups/ \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sales Team",
    "description": "Sales department group"
  }'
```

---

### Test 4: Add User to Group

First, create a regular user:

```bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@acme.com",
    "name": "Alice Johnson",
    "password": "Alice123!",
    "role": "user"
  }'
```

Then add to group:

```bash
export GROUP_ID="group-uuid-from-create-response"
export USER_ID="user-uuid-from-create-response"

curl -X POST http://localhost:8000/api/v1/groups/$GROUP_ID/members/ \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "'$USER_ID'"
  }'
```

---

### Test 5: Send Message (Group-Scoped)

```bash
curl -X POST http://localhost:8000/api/v1/messages/ \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": "'$GROUP_ID'",
    "content": "Hello team!",
    "role": "user"
  }'
```

**WebSocket Test:**
1. Open browser as Alice (group member)
2. Open another browser as Bob (NOT group member)
3. Send message to group
4. Alice should receive `message_created` event
5. Bob should NOT receive the event (group-scoped)

---

### Test 6: Upload Document (Group-Scoped)

```bash
curl -X POST http://localhost:8000/api/v1/documents/ \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "file=@/path/to/document.pdf" \
  -F "group_id=$GROUP_ID"
```

**Expected:** Group members receive `document_updated` WebSocket event

---

### Test 7: Create MCP Server (Tenant-Scoped)

```bash
curl -X POST http://localhost:8000/api/v1/mcp/ \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GitHub MCP",
    "description": "GitHub integration",
    "url": "https://api.github.com",
    "api_key": "ghp_encrypted_key"
  }'
```

---

### Test 8: Create Tool (Tenant-Scoped)

```bash
curl -X POST http://localhost:8000/api/v1/tools/ \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weather Lookup",
    "description": "Get current weather",
    "code": "def get_weather(city): return {\"temp\": 72}",
    "parameters": {"type": "object", "properties": {"city": {"type": "string"}}}
  }'
```

---

### Test 9: Set Permissions (Resource-Level)

```bash
# Grant Alice permission to execute specific agent
export AGENT_ID="agent-uuid"

curl -X POST http://localhost:8000/api/v1/permissions/ \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "user",
    "subject_id": "'$USER_ID'",
    "resource": "agent",
    "resource_id": "'$AGENT_ID'",
    "action": "execute",
    "granted": true
  }'
```

---

### Test 10: Update Tenant Settings (Tenant-Wide)

```bash
curl -X PATCH http://localhost:8000/api/v1/tenants/settings/update_current/ \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "logo_url": "https://acme.com/logo.png",
    "primary_color": "#FF5733"
  }'
```

**Expected:** ALL users in tenant receive `settings_updated` WebSocket event

---

### Test 11: Superadmin - View Tenant Stats

```bash
# Login as superadmin
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "superadmin@agentverse.com",
    "password": "SuperAdminPass123!"
  }'

export SUPERADMIN_TOKEN="superadmin-jwt-token"

# Get tenant stats
curl -X GET http://localhost:8000/api/v1/analytics/admin/tenant-stats/ \
  -H "Authorization: Bearer $SUPERADMIN_TOKEN"
```

**Expected Response:**
```json
[
  {
    "tenant_name": "Acme Corporation",
    "date": "2025-11-20",
    "total_users": 2,
    "total_agents": 1,
    "total_groups": 1,
    "messages_sent_today": 5,
    "storage_used_mb": 123.45
  },
  {
    "tenant_name": "Bharat Tech Pvt Ltd",
    "date": "2025-11-20",
    "total_users": 1,
    "total_agents": 0,
    "total_groups": 0,
    "messages_sent_today": 0,
    "storage_used_mb": 0
  }
]
```

---

### Test 12: Superadmin - Create New Tenant

```bash
curl -X POST http://localhost:8000/api/v1/tenants/admin/tenants/ \
  -H "Authorization: Bearer $SUPERADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TechStart Inc",
    "slug": "techstart",
    "email": "contact@techstart.io",
    "admin_name": "Sarah Chen",
    "admin_email": "sarah@techstart.io",
    "admin_password": "TechStart123!",
    "license_type": "pro",
    "company_size": "11-50",
    "industry": "SaaS"
  }'
```

**Expected:** New tenant + schema + domain + admin user created

---

### Test 13: Superadmin - Create Support Ticket

```bash
curl -X POST http://localhost:8000/api/v1/analytics/admin/tickets/ \
  -H "Authorization: Bearer $SUPERADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant": "acme-tenant-uuid",
    "subject": "Billing Question",
    "description": "Need clarification on invoice",
    "raised_by_email": "john@acme.com",
    "raised_by_name": "John Doe",
    "priority": "medium",
    "category": "billing"
  }'
```

---

### Test 14: License Enforcement

**Test Case:** Tenant exceeds message limit

1. Set Acme Corp to free tier (max 10,000 messages/month)
2. Send 10,001 messages
3. Next message should return:

```json
{
  "error": "Monthly message limit exceeded"
}
```

**Test in Django shell:**

```python
from apps.tenants.models import Tenant
from django.db import connection

acme = Tenant.objects.get(slug='acme')
acme.license_type = 'free'
acme.messages_this_month = 10001
acme.save()

# Try to send message - should be blocked by LicenseEnforcementMiddleware
```

---

## Testing WebSocket Real-Time Sync

### Test WebSocket Connection

Create a simple WebSocket client:

```python
# test_websocket.py
import asyncio
import websockets
import json

async def test_websocket():
    # Get JWT from login
    jwt_token = "your-jwt-token"

    uri = "ws://localhost:8000/ws/sync/"
    headers = {
        "Authorization": f"Bearer {jwt_token}"
    }

    async with websockets.connect(uri, extra_headers=headers) as websocket:
        print("✅ Connected to WebSocket")

        # Listen for broadcasts
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"📨 Received: {data['type']}")
            print(f"   Data: {data['data']}")

asyncio.run(test_websocket())
```

Run test:
```bash
python test_websocket.py
```

Then in another terminal, create an agent:
```bash
curl -X POST http://localhost:8000/api/v1/agents/ \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Agent", ...}'
```

**Expected:** WebSocket client receives `agent_updated` event instantly.

---

## Verification Checklist

### ✅ Cloud Backend

- [ ] PostgreSQL running and accessible
- [ ] Redis running and accessible
- [ ] Migrations applied successfully
- [ ] Superuser created
- [ ] Two tenants created (Acme, Bharat)
- [ ] Django admin accessible at `http://localhost:8000/admin/`
- [ ] API endpoints accessible
- [ ] WebSocket connections working

### ✅ Local Backend

- [ ] Dependencies installed
- [ ] `.env` configured
- [ ] SQLite database created
- [ ] Server running on port 8001
- [ ] API docs accessible at `http://localhost:8001/docs`

### ✅ Local Frontend

- [ ] Dependencies installed
- [ ] `.env` configured
- [ ] Development server running on port 5173
- [ ] Can access login page
- [ ] Can login with test credentials

### ✅ Data Flow Tests

- [ ] Authentication works (3-field login)
- [ ] Agent creation broadcasts to all tenant users
- [ ] Message creation broadcasts to group members only
- [ ] Settings update broadcasts to all tenant users
- [ ] Document upload triggers real-time event
- [ ] Permissions enforce access control
- [ ] License limits block over-usage
- [ ] Superadmin can view stats
- [ ] Superadmin cannot see message content
- [ ] Superadmin can create tenants

---

## Troubleshooting

### Issue: "django.db.utils.OperationalError: FATAL:  role ... does not exist"

**Solution:**
```bash
sudo -u postgres createuser -s agentverse_user
```

### Issue: "Connection refused (Redis)"

**Solution:**
```bash
sudo service redis-server start
redis-cli ping  # Should return PONG
```

### Issue: "ModuleNotFoundError: No module named 'channels'"

**Solution:**
```bash
pip install channels channels-redis
```

### Issue: WebSocket closes immediately

**Solution:** Check JWT token in Authorization header, ensure user has tenant access

### Issue: "Tenant matching query does not exist"

**Solution:** Run tenant creation script in Django shell (Step 10 of Cloud Backend Setup)

---

## Next Steps

1. **Production Deployment:**
   - Use Gunicorn + Daphne for cloud backend
   - Use Nginx as reverse proxy
   - Use PostgreSQL RDS (AWS) or managed PostgreSQL
   - Use Redis ElastiCache or managed Redis
   - Set DEBUG=False
   - Use proper SECRET_KEY

2. **Security Hardening:**
   - Enable HTTPS (SSL certificates)
   - Set secure CORS origins
   - Use environment-specific secrets
   - Enable CSRF protection
   - Set up rate limiting

3. **Monitoring:**
   - Set up Sentry for error tracking
   - Use Prometheus + Grafana for metrics
   - Monitor WebSocket connections
   - Track database query performance

---

**Version:** 1.0
**Last Updated:** 2025-11-20
**Status:** ✅ Ready for Testing
