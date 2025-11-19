# 🧪 Testing Guide - AgentVerse Local ↔ Cloud Communication

**Status:** Ready to test!
**Date:** 2025-11-19

---

## 🎯 What We're Testing

1. **Cloud Backend** (Django) - Multi-tenant SaaS APIs
2. **Local Backend** (FastAPI) - Desktop app backend with cloud proxy
3. **Communication** - Local → Cloud authentication and data sync
4. **Caching** - Local cache of cloud data for offline execution

---

## 📋 Prerequisites

### **Cloud Backend:**
- Python 3.11+
- PostgreSQL OR SQLite (for quick testing)
- Redis (optional, for Celery)

### **Local Backend:**
- Python 3.11+
- Dependencies from local_backend/requirements.txt

---

## ⚡ Quick Start - Test Both Backends

### **Terminal 1: Start Cloud Backend (Django)**

```bash
cd cloud_backend

# Quick setup with SQLite (for testing)
chmod +x quickstart.sh
./quickstart.sh

# OR manual setup:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Use SQLite for quick testing (no PostgreSQL needed)
export DATABASE_URL="sqlite:///./db.sqlite3"

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
# Enter: admin@example.com / password123

# Run server on port 9000
python manage.py runserver 9000
```

**Expected output:**
```
Starting development server at http://127.0.0.1:9000/
```

---

### **Terminal 2: Start Local Backend (FastAPI)**

```bash
cd local_backend

# Activate virtual environment (if you have one)
source venv/bin/activate  # or create: python3 -m venv venv

# Install dependencies
pip install -r requirements.txt

# Configure cloud connection
# Edit .env or export:
export CLOUD_ENABLED=true
export CLOUD_BASE_URL=http://localhost:9000

# Run server (default port 8000)
python server.py
```

**Expected output:**
```
✅ Cloud integration enabled - initializing...
✅ Cloud client initialized: http://localhost:9000
✅ Local cache initialized: ./data/cache
⚠️  No cloud token - skipping data sync (login required)
✅ Backend Server: Initialized with 0 agents
```

---

## 🧪 Test Scenarios

### **Test 1: Health Checks**

```bash
# Test cloud backend
curl http://localhost:9000/health/
# Expected: {"status":"healthy","service":"agentverse-cloud","version":"1.0.0"}

# Test local backend
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"agentverse-backend",...}
```

---

### **Test 2: Cloud Backend Authentication**

```bash
# Login directly to cloud backend
curl -X POST http://localhost:9000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password123"}'

# Expected response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "email": "admin@example.com",
    "name": "Admin User",
    "role": "admin"
  },
  "tenant_id": "uuid",
  "user_role": "admin"
}

# Save the access_token for next requests
export TOKEN="<access_token_from_response>"
```

---

### **Test 3: Cloud Backend CRUD**

```bash
# Create an agent (admin only)
curl -X POST http://localhost:9000/api/v1/agents/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Research Assistant",
    "description": "Helps with research tasks",
    "emoji": "🔬",
    "llm_provider": "anthropic",
    "llm_model": "claude-sonnet-4.5",
    "system_prompt": "You are a helpful research assistant.",
    "config": {"temperature": 0.2}
  }'

# Expected: Agent created with ID

# List agents
curl http://localhost:9000/api/v1/agents/ \
  -H "Authorization: Bearer $TOKEN"

# Expected: Array of agents
```

---

### **Test 4: Local → Cloud Proxy Authentication**

```bash
# Login via local backend (proxies to cloud)
curl -X POST http://localhost:8000/api/v1/cloud/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password123"}'

# Expected:
# 1. Authentication with cloud backend
# 2. JWT tokens returned
# 3. Local cache synced with tenant data
# 4. Console logs show sync progress

# Check local cache status
curl http://localhost:8000/api/v1/cloud/cache/status

# Expected:
{
  "last_sync": "2025-11-19T12:34:56",
  "counts": {
    "agents": 1,
    "tools": 0,
    "mcp_servers": 0,
    "groups": 0,
    "users": 1
  }
}
```

---

### **Test 5: Cache Refresh**

```bash
# After creating data in cloud, manually refresh cache
curl -X POST http://localhost:8000/api/v1/cloud/cache/refresh

# Expected: "Cache refreshed successfully"

# Verify cache updated
curl http://localhost:8000/api/v1/cloud/cache/status
```

---

### **Test 6: Direct Cloud Data Access (Bypass Cache)**

```bash
# Get agents from cloud (bypasses cache)
curl http://localhost:8000/api/v1/cloud/agents

# Get tools from cloud
curl http://localhost:8000/api/v1/cloud/tools

# Get MCP servers from cloud
curl http://localhost:8000/api/v1/cloud/mcp-servers
```

---

## 🔍 Debugging

### **Cloud Backend Logs:**
Check Terminal 1 for Django logs:
```
"POST /api/v1/auth/login HTTP/1.1" 200 ...
"GET /api/v1/agents/ HTTP/1.1" 200 ...
```

### **Local Backend Logs:**
Check Terminal 2 for FastAPI logs:
```
INFO: Logging in user: admin@example.com
INFO: Login successful. Tenant: uuid, Role: admin
INFO: Syncing tenant data from cloud...
INFO: ✅ Cloud data synced to local cache
```

### **Check Cache Database:**
```bash
cd local_backend
sqlite3 data/cache/cloud_data.db

# Check tables
.tables
# Expected: agents, tools, mcp_servers, groups, users, cache_metadata

# Check cached agents
SELECT * FROM agents;
```

---

## 🚨 Common Issues

### **Issue 1: "Cloud client not initialized"**
**Solution:** Make sure `CLOUD_ENABLED=true` in local backend .env

### **Issue 2: "Connection refused to localhost:9000"**
**Solution:** Start cloud backend first

### **Issue 3: "401 Unauthorized"**
**Solution:** Login first to get valid JWT token

### **Issue 4: "ImportError: No module named 'django_tenants'"**
**Solution:** Install cloud backend dependencies:
```bash
cd cloud_backend
pip install -r requirements.txt
```

### **Issue 5: "table agents does not exist"**
**Solution:** Run migrations:
```bash
cd cloud_backend
python manage.py makemigrations
python manage.py migrate
```

---

## ✅ Success Criteria

After testing, you should have:

1. ✅ Cloud backend running on port 9000
2. ✅ Local backend running on port 8000
3. ✅ Successfully logged in via local backend
4. ✅ Local cache populated with cloud data
5. ✅ Can create/read agents via cloud backend
6. ✅ Cache status shows synced data

---

## 📊 Architecture Flow (What's Happening)

```
Frontend (React)
    ↓
    POST /api/v1/cloud/auth/login
    ↓
Local Backend (FastAPI:8000)
    ↓
    POST http://localhost:9000/api/v1/auth/login
    ↓
Cloud Backend (Django:9000)
    ↓
    Query PostgreSQL/SQLite
    ↓
    Return JWT + User Data
    ↓
Local Backend
    ↓
    Sync to SQLite Cache
    ↓
    Return to Frontend

Execution Flow:
Frontend → Local Backend → Uses Cached Agents/Tools → Execute Locally
CRUD Flow:
Frontend → Local Backend → Proxy to Cloud → Update DB → Refresh Cache
```

---

## 🎯 Next Steps After Testing

Once both backends are communicating:

1. **Frontend Integration** - Add login screen
2. **CRUD Integration** - Update frontend to use cloud APIs
3. **Real-Time Sync** - Add WebSocket for live updates
4. **Production Deploy** - Deploy cloud backend to Render.com

---

## 📝 Test Checklist

- [ ] Cloud backend starts without errors
- [ ] Local backend starts without errors
- [ ] Health checks pass for both
- [ ] Can login to cloud directly
- [ ] Can create agent via cloud API
- [ ] Can login via local backend proxy
- [ ] Local cache syncs after login
- [ ] Cache status shows correct counts
- [ ] Can refresh cache manually
- [ ] Can query cloud data via proxy

---

**Status:** Ready to test! Start both backends and follow the test scenarios above.

**Branch:** `claude/analyze-codebase-01K75G9B3QPJtgZggyUqF3dQ`
**Last Update:** 2025-11-19
