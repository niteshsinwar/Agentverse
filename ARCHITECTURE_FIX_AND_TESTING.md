# Architecture Fix & Comprehensive Testing Plan

**Date:** 2025-11-20
**Critical Issue:** Frontend calling cloud backend directly (violates architecture)

---

## ⚠️ ARCHITECTURAL VIOLATION FOUND

### Current (WRONG):
```
local_frontend:1420 ──HTTP──> cloud_backend:9000 ❌
```

### Required (CORRECT):
```
local_frontend:1420 ──HTTP──> local_backend:8000 ──HTTP──> cloud_backend:9000 ✅
```

---

## 🔧 FIXES REQUIRED

### 1. Frontend Configuration Fix

**File:** `local_frontend/src/lib/cloud/config.ts`

**Current (Line 19):**
```typescript
const baseUrl = import.meta.env.VITE_CLOUD_BASE_URL || 'http://localhost:9000';
```

**Fix To:**
```typescript
// All cloud requests go through local_backend proxy
const baseUrl = import.meta.env.VITE_LOCAL_BACKEND_URL || 'http://localhost:8000';
```

**Impact:** ALL `cloudHttpClient` requests will now route through local_backend proxy.

---

### 2. Frontend Environment Variables

**File:** `local_frontend/.env` (create if not exists)

```bash
# Local Backend (proxy to cloud)
VITE_LOCAL_BACKEND_URL=http://localhost:8000

# Cloud features enabled (but accessed via local_backend proxy)
VITE_CLOUD_ENABLED=true

# WebSocket goes through local_backend too
VITE_WS_URL=ws://localhost:8000
```

---

### 3. Update Frontend API Calls

**Current endpoints in httpClient:**
- Direct cloud calls: `/api/v1/agents/`, `/api/v1/tools/`, etc.

**New proxy endpoints (via local_backend):**
- `/api/v1/cloud/agents` ← Proxy to cloud
- `/api/v1/cloud/tools` ← Proxy to cloud
- `/api/v1/cloud/auth/login` ← Already correct!

**Action:** Update all cloud service files to use `/cloud/` prefix.

---

## 📋 COMPREHENSIVE TESTING PLAN

### Phase 1: Unit Testing

#### A. Cloud Backend Tests
```bash
cd cloud_backend
pip install -r requirements.txt
pytest apps/agents/tests/ -v
pytest apps/tools/tests/ -v
pytest apps/users/tests/ -v
pytest apps/tenants/tests/ -v
pytest apps/analytics/tests/ -v
```

#### B. Local Backend Tests
```bash
cd local_backend
pip install -r requirements.txt
pytest tests/unit/ -v
pytest tests/api/ -v
```

#### C. Local Frontend Tests
```bash
cd local_frontend
npm install
npm run test
npm run lint
```

---

### Phase 2: Setup & Configuration

#### A. Cloud Backend Setup

**1. PostgreSQL Database:**
```bash
# Create database
createdb agentverse_cloud

# Or use Docker
docker run -d \
  --name agentverse-postgres \
  -e POSTGRES_DB=agentverse_cloud \
  -e POSTGRES_USER=agentverse \
  -e POSTGRES_PASSWORD=agentverse123 \
  -p 5432:5432 \
  postgres:15
```

**2. Redis:**
```bash
# Use Docker
docker run -d \
  --name agentverse-redis \
  -p 6379:6379 \
  redis:7-alpine
```

**3. Environment Variables:**
```bash
# cloud_backend/.env
DATABASE_URL=postgresql://agentverse:agentverse123@localhost:5432/agentverse_cloud
REDIS_URL=redis://localhost:6379/0
DJANGO_SECRET_KEY=your-secret-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:8000,http://localhost:1420
```

**4. Migrations:**
```bash
cd cloud_backend
python manage.py migrate_schemas --shared
python manage.py migrate_schemas
python manage.py collectstatic --noinput
```

**5. Create Superuser:**
```bash
python manage.py createsuperuser
# Email: admin@agentverse.com
# Password: admin123
```

**6. Start Server:**
```bash
python manage.py runserver 9000
```

---

#### B. Local Backend Setup

**1. Environment Variables:**
```bash
# local_backend/.env
CLOUD_BACKEND_URL=http://localhost:9000
CLOUD_BACKEND_WS_URL=ws://localhost:9000
DATABASE_URL=sqlite:///~/.agentverse/local.db
LOG_LEVEL=INFO
```

**2. Start Server:**
```bash
cd local_backend
uvicorn src.main:app --reload --port 8000
```

---

#### C. Local Frontend Setup

**1. Fix Configuration (as described above)**

**2. Environment Variables:**
```bash
# local_frontend/.env
VITE_LOCAL_BACKEND_URL=http://localhost:8000
VITE_CLOUD_ENABLED=true
VITE_WS_URL=ws://localhost:8000
```

**3. Start Dev Server:**
```bash
cd local_frontend
npm run dev
```

---

### Phase 3: Integration Testing

#### Test 1: Authentication Flow
```
Step 1: Frontend login form
  ↓
Step 2: POST localhost:8000/api/v1/cloud/auth/login
  ↓
Step 3: local_backend proxies to localhost:9000/api/v1/auth/login
  ↓
Step 4: cloud_backend validates + returns JWT
  ↓
Step 5: local_backend caches data + returns to frontend
  ↓
Step 6: Frontend stores tokens + redirects

✅ Verify: No direct calls to :9000
✅ Verify: Cache populated in local_backend
✅ Verify: Frontend has user context
```

#### Test 2: Agent Creation (Admin)
```
Step 1: Admin creates agent in frontend
  ↓
Step 2: POST localhost:8000/api/v1/cloud/agents
  ↓
Step 3: local_backend proxies to localhost:9000/api/v1/agents/
  ↓
Step 4: cloud_backend creates agent + triggers signal
  ↓
Step 5: Django signal broadcasts via WebSocket
  ↓
Step 6: local_backend receives WS event + updates cache
  ↓
Step 7: Frontend receives WS event + updates UI

✅ Verify: Agent created in cloud DB
✅ Verify: Agent cached in local_backend
✅ Verify: Frontend UI updated in real-time
✅ Verify: All devices of same tenant receive update
```

#### Test 3: Group Message (Real-Time Sync)
```
Step 1: User sends message in group
  ↓
Step 2: POST localhost:8000/api/v1/cloud/messages/
  ↓
Step 3: local_backend proxies to cloud
  ↓
Step 4: cloud_backend saves message + broadcasts to group channel
  ↓
Step 5: All group members receive WS event
  ↓
Step 6: Frontend updates conversation in real-time

✅ Verify: Message in cloud DB
✅ Verify: All group members see message instantly
✅ Verify: Execution context tracked correctly
```

#### Test 4: Multi-Device Sync
```
Setup: Same user logged in on 2 devices
  Device A: Desktop
  Device B: Laptop

Test: Device A creates agent
  ↓
Device B receives WebSocket broadcast
  ↓
Device B UI updates automatically

✅ Verify: Both devices synced
✅ Verify: Both devices joined sync_{tenant_id} channel
✅ Verify: Device-specific routing works (device_{device_id})
```

#### Test 5: Permission Enforcement
```
Test: Regular user tries to create agent (admin-only action)
  ↓
Expected: 403 Forbidden

Test: Regular user views agents
  ↓
Expected: Success (filtered by permissions)

✅ Verify: Admin vs User roles enforced
✅ Verify: Permission-based filtering works
```

---

### Phase 4: Performance Testing

#### A. Load Testing
```bash
# Install k6
brew install k6  # or appropriate package manager

# Run load test
k6 run scripts/load_test.js
```

#### B. WebSocket Stress Test
```
Scenario: 100 concurrent users in same group
Action: Send 1000 messages rapidly
Metrics:
  - Message delivery latency
  - WebSocket connection stability
  - Database query performance
  - Cache hit rate
```

---

### Phase 5: Security Testing

#### A. Authentication
```
✅ Test: Login without credentials → 401
✅ Test: Login with wrong password → 401
✅ Test: Access protected endpoint without token → 401
✅ Test: Access with expired token → 401 → Auto-refresh
✅ Test: Cross-tenant access → 403
```

#### B. Authorization
```
✅ Test: User access admin-only endpoint → 403
✅ Test: User access other tenant's data → 403
✅ Test: User access group they're not member of → 403
```

#### C. Input Validation
```
✅ Test: SQL injection attempts
✅ Test: XSS attempts
✅ Test: CSRF attacks (should be blocked)
✅ Test: Oversized payloads
```

---

## 🎯 SUCCESS CRITERIA

### Must Pass:
1. ✅ **No direct frontend → cloud calls** (all via local_backend proxy)
2. ✅ **Unit tests pass** for all 3 codebases (>80% coverage)
3. ✅ **Integration tests pass** for all flows
4. ✅ **Real-time sync works** across multiple devices
5. ✅ **Role-based access control** enforced
6. ✅ **Tenant isolation** verified (no cross-tenant leaks)
7. ✅ **WebSocket broadcasting** works for all event types
8. ✅ **Cache synchronization** works correctly
9. ✅ **Execution context** tracked through agent chains
10. ✅ **Performance acceptable** (<500ms API responses)

---

## 📊 TESTING CHECKLIST

### Cloud Backend (/cloud_backend)
- [ ] PostgreSQL connected and migrated
- [ ] Redis connected
- [ ] Django admin accessible (http://localhost:9000/admin/)
- [ ] Grappelli UI working
- [ ] Superuser created
- [ ] Test tenant created via admin
- [ ] WebSocket endpoint accessible
- [ ] All CRUD endpoints responding
- [ ] Django signals firing correctly
- [ ] Tenant isolation working

### Local Backend (/local_backend)
- [ ] FastAPI running (http://localhost:8000/docs)
- [ ] Cloud proxy endpoints available
- [ ] Cache initialized
- [ ] Device ID generated
- [ ] WebSocket client connected to cloud
- [ ] Proxy authentication working
- [ ] Cache sync working
- [ ] All proxy endpoints responding

### Local Frontend (/local_frontend)
- [ ] Vite dev server running (http://localhost:1420)
- [ ] Login page accessible
- [ ] 3-field login form (tenant_id, email, password)
- [ ] NO direct cloud backend calls
- [ ] ALL calls go through localhost:8000
- [ ] WebSocket connected to local_backend
- [ ] Real-time updates working
- [ ] UI responsive and styled correctly

---

## 🚀 EXECUTION COMMAND SEQUENCE

```bash
# Terminal 1: Cloud Backend
cd cloud_backend
source venv/bin/activate  # or create venv first
pip install -r requirements.txt
python manage.py migrate_schemas --shared
python manage.py migrate_schemas
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py runserver 9000

# Terminal 2: Local Backend
cd local_backend
source venv/bin/activate  # or create venv first
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# Terminal 3: Local Frontend
cd local_frontend
npm install
npm run dev

# Terminal 4: Testing
# Run tests as needed
```

---

## 📝 NOTES

- **Architecture Rule:** Frontend MUST NEVER call cloud backend directly
- **All communication:** Frontend → Local Backend → Cloud Backend
- **WebSocket:** Also proxied through local backend
- **Caching:** Local backend caches all cloud data for offline capability
- **Real-time:** WebSocket events broadcast to all connected devices
- **Isolation:** Tenant data completely isolated (schema-based)

---

**Version:** 1.0
**Status:** Ready for Implementation
**Last Updated:** 2025-11-20
