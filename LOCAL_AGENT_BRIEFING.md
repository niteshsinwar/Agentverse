# Local Agent Briefing - AgentVerse Multi-Tenant System

**Your Role:** Testing, debugging, database setup, and providing feedback on code issues.
**My Role (Cloud Agent):** Fixing code based on your feedback.

---

## SYSTEM OVERVIEW

**AgentVerse** is a multi-tenant AI agent platform with 3 codebases:

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│ local_frontend  │──────▶│ local_backend    │──────▶│ cloud_backend   │
│ (React/Vite)    │      │ (FastAPI)        │      │ (Django)        │
│ Port: 1420      │      │ Port: 8000       │      │ Port: 9000      │
│                 │      │ Proxy Layer      │      │ Multi-Tenant DB │
└─────────────────┘      └──────────────────┘      └─────────────────┘
```

### Architecture Rules:
1. **Frontend MUST NEVER call cloud_backend directly**
2. **All requests go through local_backend proxy**
3. **Cloud backend enforces tenant isolation via JWT**
4. **PostgreSQL uses schema-based multi-tenancy (django-tenants)**

---

## WHAT WAS DONE (Cloud Agent)

### 1. AdminView.tsx Integration (COMPLETED)

**Issue:** AdminView showed hardcoded mock data for all tenants.

**Fix Applied:**
- Created `/local_frontend/src/lib/cloud/api.ts` - Cloud API client
- Updated `/local_frontend/src/components/views/AdminView.tsx` to fetch real data
- Removed all mock data (mockUsers, mockGroups, mockResources)
- Added loading states, error states, empty states

**Files Changed:**
- `local_frontend/src/lib/cloud/api.ts` (NEW)
- `local_frontend/src/components/views/AdminView.tsx` (MODIFIED)

**Commit:** `66d8a47` - "✨ Integrate AdminView with real cloud backend API"

### 2. Previous Fixes (Already Deployed)

**Commit `baa0ca7` (by previous local agent):**
- Fixed Grappelli admin crash (`'bool' object is not callable`)
- Fixed local_backend startup crash (`NameError: name 'Field' is not defined`)
- Added `tenant_id` to LoginRequest model
- Added `/auth/me` endpoint in cloud_proxy.py
- Added colored tenant badges in Django admin

---

## CURRENT STATE

### ✅ Working:
- Local frontend can compile and run
- Local backend can start (port 8000)
- Cloud backend Django is configured
- Grappelli admin theme installed
- JWT authentication flow implemented
- Cloud API client created

### ❌ Blocked:
- **PostgreSQL not running** → migrations can't be applied
- **No database** → no tenant schemas exist
- **No test data** → AdminView shows empty states
- **Can't test tenant isolation** → no tenants created

---

## YOUR TASKS

### TASK 1: Start PostgreSQL Database

**Check if PostgreSQL is running:**
```bash
pg_isready -h localhost -p 5432
```

**If not running, try one of these:**

#### Option A: Docker (PREFERRED)
```bash
# Start PostgreSQL
docker run -d --name agentverse-postgres \
  -e POSTGRES_DB=agentverse_cloud \
  -e POSTGRES_USER=agentverse \
  -e POSTGRES_PASSWORD=agentverse123 \
  -p 5432:5432 postgres:15

# Start Redis (needed for Django Channels/WebSocket)
docker run -d --name agentverse-redis \
  -p 6379:6379 redis:7-alpine

# Verify
docker ps
pg_isready -h localhost -p 5432
```

#### Option B: System PostgreSQL Service
```bash
# Check status
sudo systemctl status postgresql

# Start if available
sudo systemctl start postgresql

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE agentverse_cloud;"
sudo -u postgres psql -c "CREATE USER agentverse WITH PASSWORD 'agentverse123';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE agentverse_cloud TO agentverse;"
```

#### Option C: Report if neither works
**Feedback to provide:**
```
ISSUE: Cannot start PostgreSQL
- Docker available: [YES/NO]
- Systemctl available: [YES/NO]
- Alternative approach needed: [DESCRIBE]
```

---

### TASK 2: Create Environment Configuration

**File:** `/home/user/Agentverse/cloud_backend/.env`

```bash
cd /home/user/Agentverse/cloud_backend
cp .env.example .env
```

**Edit `.env` with:**
```env
DJANGO_SECRET_KEY=dev-secret-key-change-in-production-min-50-chars-long
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://agentverse:agentverse123@localhost:5432/agentverse_cloud
REDIS_URL=redis://localhost:6379/0
CORS_ALLOWED_ORIGINS=http://localhost:8000,http://localhost:1420
```

**Test configuration:**
```bash
cd /home/user/Agentverse/cloud_backend
source venv/bin/activate
python manage.py check
```

**Expected:** No errors

**If errors occur, provide feedback:**
```
ERROR: Django check failed
Error message: [COPY EXACT ERROR]
Stack trace: [COPY IF AVAILABLE]
```

---

### TASK 3: Apply Database Migrations

```bash
cd /home/user/Agentverse/cloud_backend
source venv/bin/activate

# Step 1: Migrate shared apps (tenants, users, core)
python manage.py migrate_schemas --shared

# Step 2: Migrate tenant-specific apps (agents, tools, groups, etc.)
python manage.py migrate_schemas

# Step 3: Verify migrations
python manage.py showmigrations
```

**Expected Output:**
```
admin
  [X] 0001_initial
  [X] 0002_logentry_remove_auto_add
  ...
tenants
  [X] 0001_initial
agents
  [X] 0001_initial
  [X] 0002_add_tenant_field
groups
  [X] 0001_initial
  [X] 0002_add_tenant_field
...
```

**If migration fails, provide feedback:**
```
ERROR: Migration failed
Command: [EXACT COMMAND]
Error: [EXACT ERROR MESSAGE]
Traceback: [FULL TRACEBACK]
```

---

### TASK 4: Create Superuser

```bash
cd /home/user/Agentverse/cloud_backend
source venv/bin/activate
python manage.py createsuperuser
```

**Input:**
- Email: `admin@agentverse.com`
- Password: `admin123` (or your choice)

**Test Django Admin:**
```bash
# Start cloud backend
python manage.py runserver 9000
```

**In browser:** `http://localhost:9000/admin/`
- Login with superuser credentials
- Should see Grappelli-themed admin panel

**Feedback if it works:**
```
SUCCESS: Django admin accessible
- Grappelli theme: [VISIBLE/NOT VISIBLE]
- Can see Tenants model: [YES/NO]
```

---

### TASK 5: Create Test Tenants

**Via Django Shell:**
```bash
cd /home/user/Agentverse/cloud_backend
source venv/bin/activate
python manage.py shell
```

**In Python shell:**
```python
from apps.tenants.models import Tenant, Domain
from apps.users.models import User
from django_tenants.utils import schema_context

# Create Bharat Tech tenant
bharat = Tenant.objects.create(
    schema_name='bharattech',
    name='Bharat Tech',
    slug='bharattech',
    is_active=True
)
Domain.objects.create(
    domain='bharattech.localhost',
    tenant=bharat,
    is_primary=True
)
print(f"✅ Created tenant: {bharat.name} (schema: {bharat.schema_name})")

# Create Acme Corp tenant
acme = Tenant.objects.create(
    schema_name='acmecorp',
    name='Acme Corp',
    slug='acmecorp',
    is_active=True
)
Domain.objects.create(
    domain='acmecorp.localhost',
    tenant=acme,
    is_primary=True
)
print(f"✅ Created tenant: {acme.name} (schema: {acme.schema_name})")

# Create admin user for Bharat Tech
with schema_context('bharattech'):
    bharat_admin = User.objects.create_user(
        email='admin@bharattech.com',
        name='Bharat Admin',
        password='password123',
        role='admin'
    )
    print(f"✅ Created admin: {bharat_admin.email}")

# Create admin user for Acme Corp
with schema_context('acmecorp'):
    acme_admin = User.objects.create_user(
        email='admin@acmecorp.com',
        name='Acme Admin',
        password='password123',
        role='admin'
    )
    print(f"✅ Created admin: {acme_admin.email}")

# Verify
print(f"\nTotal tenants: {Tenant.objects.count()}")
```

**Expected Output:**
```
✅ Created tenant: Bharat Tech (schema: bharattech)
✅ Created tenant: Acme Corp (schema: acmecorp)
✅ Created admin: admin@bharattech.com
✅ Created admin: admin@acmecorp.com

Total tenants: 2
```

**If errors occur:**
```
ERROR: Tenant creation failed
Step: [Which step failed]
Error: [EXACT ERROR]
```

---

### TASK 6: Create Test Groups

**Continue in Django shell:**
```python
from apps.groups.models import Group

# Bharat Tech groups
with schema_context('bharattech'):
    eng = Group.objects.create(
        name='Engineering',
        description='Bharat Tech software development team',
    )
    ds = Group.objects.create(
        name='Data Science',
        description='Bharat Tech ML and AI research team',
    )
    print(f"✅ Created {Group.objects.count()} groups for Bharat Tech")

# Acme Corp groups
with schema_context('acmecorp'):
    sales = Group.objects.create(
        name='Sales',
        description='Acme Corp sales team',
    )
    support = Group.objects.create(
        name='Support',
        description='Acme Corp customer support team',
    )
    product = Group.objects.create(
        name='Product',
        description='Acme Corp product management',
    )
    print(f"✅ Created {Group.objects.count()} groups for Acme Corp")

# Verify isolation
with schema_context('bharattech'):
    print(f"Bharat Tech groups: {list(Group.objects.values_list('name', flat=True))}")

with schema_context('acmecorp'):
    print(f"Acme Corp groups: {list(Group.objects.values_list('name', flat=True))}")
```

**Expected Output:**
```
✅ Created 2 groups for Bharat Tech
✅ Created 3 groups for Acme Corp
Bharat Tech groups: ['Engineering', 'Data Science']
Acme Corp groups: ['Sales', 'Support', 'Product']
```

---

### TASK 7: Start All Services

**Terminal 1 - Cloud Backend:**
```bash
cd /home/user/Agentverse/cloud_backend
source venv/bin/activate
python manage.py runserver 9000
```

**Expected:** Server starts without errors on port 9000

**Terminal 2 - Local Backend:**
```bash
cd /home/user/Agentverse/local_backend
source venv/bin/activate
uvicorn src.main:app --reload --port 8000
```

**Expected:** FastAPI starts on port 8000

**Terminal 3 - Local Frontend:**
```bash
cd /home/user/Agentverse/local_frontend
npm run dev
```

**Expected:** Vite dev server on port 1420

**Provide startup status:**
```
STARTUP STATUS:
- Cloud backend (9000): [RUNNING/FAILED - error if failed]
- Local backend (8000): [RUNNING/FAILED - error if failed]
- Frontend (1420): [RUNNING/FAILED - error if failed]
```

---

### TASK 8: Test Tenant Isolation

#### Test 1: Bharat Tech Login

1. **Open browser:** `http://localhost:1420`

2. **Login with:**
   - Tenant ID: `bharattech`
   - Email: `admin@bharattech.com`
   - Password: `password123`

3. **Expected:**
   - Login successful
   - Redirected to dashboard
   - User name displayed: "Bharat Admin"

4. **Navigate to Admin Panel:**
   - Click "Admin" in sidebar (or wherever admin link is)
   - Click "Groups" tab

5. **CRITICAL CHECK - Expected Result:**
   - **Should see EXACTLY 2 groups:**
     - "Engineering"
     - "Data Science"
   - **Should NOT see Acme Corp groups** (Sales, Support, Product)
   - Count should show: "2 Active Groups"

6. **Open Browser DevTools → Network Tab:**
   - Check the API call to `/api/v1/cloud/groups`
   - **Should call:** `http://localhost:8000/api/v1/cloud/groups`
   - **Should NOT call:** `http://localhost:9000` directly
   - Check response - should contain only Bharat Tech groups

**Provide feedback:**
```
TEST 1: Bharat Tech Login
- Login: [SUCCESS/FAILED]
- Groups visible: [LIST EXACT GROUPS SHOWN]
- Group count: [NUMBER]
- Acme groups visible: [YES - BUG! / NO - CORRECT]
- API endpoint called: [EXACT URL]
- Response data: [COPY JSON if possible]
```

#### Test 2: Acme Corp Login

1. **Logout from Bharat Tech**

2. **Login with:**
   - Tenant ID: `acmecorp`
   - Email: `admin@acmecorp.com`
   - Password: `password123`

3. **Navigate to Admin → Groups**

4. **CRITICAL CHECK - Expected Result:**
   - **Should see EXACTLY 3 groups:**
     - "Sales"
     - "Support"
     - "Product"
   - **Should NOT see Bharat Tech groups** (Engineering, Data Science)
   - Count should show: "3 Active Groups"

**Provide feedback:**
```
TEST 2: Acme Corp Login
- Login: [SUCCESS/FAILED]
- Groups visible: [LIST EXACT GROUPS SHOWN]
- Group count: [NUMBER]
- Bharat groups visible: [YES - BUG! / NO - CORRECT]
```

#### Test 3: Cross-Contamination Check

**THIS IS THE CRITICAL TEST - User's original complaint**

**Scenario:**
User said: "when bharat tech admin login then two groups were already created and then when acme group admin login then same two group were their"

**What we're checking:**
- Do different tenants see DIFFERENT groups?
- Or do they see THE SAME hardcoded groups?

**Expected Result:**
- ✅ **Bharat Tech sees:** Engineering, Data Science (2 groups)
- ✅ **Acme Corp sees:** Sales, Support, Product (3 groups)
- ❌ **BOTH seeing same groups = BUG**

**Provide feedback:**
```
TEST 3: Cross-Contamination Check
- Bharat Tech groups: [EXACT LIST]
- Acme Corp groups: [EXACT LIST]
- Are they different: [YES - CORRECT / NO - BUG!]
- If same, groups shown: [LIST]
```

---

### TASK 9: Test Other Admin Tabs

#### Users Tab

1. **Login as Bharat Tech admin**
2. **Go to Admin → Users**

**Expected:**
- Should show 1 user: "Bharat Admin" (admin@bharattech.com)
- Or might show 0 users if `/api/v1/cloud/users` endpoint not implemented

**Provide feedback:**
```
USERS TAB:
- Users shown: [LIST USERS]
- Error message if any: [ERROR]
```

#### Resources Tab

1. **Go to Admin → Resources**

**Expected:**
- Might show 0 resources (no agents/tools/mcp servers created yet)
- Empty state message: "No resources found for this tenant"

**Provide feedback:**
```
RESOURCES TAB:
- Resources shown: [NUMBER and LIST]
- Empty state displayed: [YES/NO]
```

---

### TASK 10: Test Error Handling

#### Test Invalid Login

1. **Login with:**
   - Tenant ID: `invalidtenant`
   - Email: `test@test.com`
   - Password: `wrong`

**Expected:**
- Error message displayed
- Not redirected to dashboard

**Provide feedback:**
```
ERROR HANDLING TEST:
- Error message shown: [YES/NO]
- Error text: [EXACT MESSAGE]
- UI crashed: [YES/NO]
```

#### Test Without Authentication

1. **Logout**
2. **Try to directly access:** `http://localhost:1420/admin` (or wherever admin is)

**Expected:**
- Redirected to login
- Or error message: "Not authenticated"

**Provide feedback:**
```
AUTH CHECK:
- Redirected to login: [YES/NO]
- Error shown: [YES/NO]
- Could access admin: [YES - BUG! / NO - CORRECT]
```

---

## CRITICAL ISSUES TO REPORT

### Issue 1: Users Endpoint Missing

**File:** `local_backend/src/api/v1/endpoints/cloud_proxy.py`

**Current state:** No `/api/v1/cloud/users` endpoint exists

**Impact:** AdminView Users tab will show empty or error

**What to check:**
```bash
# Test the endpoint
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/v1/cloud/users
```

**Expected:** 404 Not Found

**Feedback to provide:**
```
ISSUE: Users endpoint not implemented
- Endpoint exists: NO
- Users tab shows: [WHAT USERS TAB SHOWS]
- Error in console: [BROWSER CONSOLE ERRORS]

CLOUD AGENT: Please create /api/v1/cloud/users endpoint in cloud_proxy.py
```

---

### Issue 2: Missing Users Endpoint in Cloud Backend

**What to check:**
```bash
# In cloud_backend venv
cd /home/user/Agentverse/cloud_backend
source venv/bin/activate
python manage.py show_urls | grep users
```

**Feedback:**
```
CLOUD BACKEND ENDPOINTS:
[LIST AVAILABLE ENDPOINTS]

CLOUD AGENT: Need to create users list endpoint in cloud backend
```

---

### Issue 3: Console Errors

**What to check:**
- Open browser DevTools → Console
- Look for JavaScript errors
- Look for failed API calls (red in Network tab)

**Provide feedback:**
```
CONSOLE ERRORS:
[COPY ALL ERRORS FROM BROWSER CONSOLE]

NETWORK ERRORS:
[LIST FAILED API CALLS WITH STATUS CODES]
```

---

## EXPECTED FINAL STATE

### ✅ Success Criteria:

1. **PostgreSQL running** on port 5432
2. **Migrations applied** - `python manage.py showmigrations` shows all `[X]`
3. **2 tenants created** - Bharat Tech, Acme Corp
4. **Tenant schemas exist** in database
5. **Admin users created** for each tenant
6. **Groups created** - different for each tenant
7. **All 3 services running** - cloud:9000, local:8000, frontend:1420
8. **Bharat Tech login works** - sees only Bharat Tech groups
9. **Acme Corp login works** - sees only Acme Corp groups
10. **NO cross-tenant data leaks** - isolation enforced

### 🎯 User's Original Complaint (Should be FIXED):

**Before:**
> "when bharat tech admin login then two groups were already created and then when acme group admin login then same two group were their"

**After (Expected):**
> Bharat Tech admin sees DIFFERENT groups than Acme Corp admin.
> Each tenant sees ONLY their own data.

---

## FEEDBACK TEMPLATE

When reporting back, use this template:

```markdown
## LOCAL AGENT REPORT

### SETUP STATUS:
- PostgreSQL: [RUNNING/FAILED]
- Migrations: [APPLIED/FAILED]
- Tenants created: [YES/NO]
- Services running: [LIST STATUS]

### TEST RESULTS:

#### Bharat Tech Login:
- Login: [SUCCESS/FAILED]
- Groups shown: [EXACT LIST]
- Group count: [NUMBER]

#### Acme Corp Login:
- Login: [SUCCESS/FAILED]
- Groups shown: [EXACT LIST]
- Group count: [NUMBER]

#### Tenant Isolation:
- Different data for each tenant: [YES/NO]
- Cross-contamination detected: [YES/NO]

### ISSUES FOUND:

1. [Issue description]
   - File: [filename]
   - Error: [exact error]
   - Request to Cloud Agent: [what to fix]

2. [Next issue]
   ...

### CONSOLE ERRORS:
[Copy browser console errors]

### SCREENSHOTS/EVIDENCE:
[Describe what you see in the UI]
```

---

## SUMMARY

**Your Mission:**
1. Set up PostgreSQL database
2. Apply all migrations
3. Create test tenants and data
4. Start all services
5. Test tenant isolation in AdminView
6. Report any bugs or issues
7. Provide feedback for code fixes

**My Mission (Cloud Agent):**
1. Wait for your feedback
2. Fix any code issues you find
3. Create missing endpoints
4. Update configurations as needed

**Communication Flow:**
- User will copy-paste your feedback to me
- I will fix code and respond
- User will copy-paste my response back to you
- Repeat until everything works

**Goal:**
- Prove that AdminView now shows REAL tenant-specific data
- Confirm Bharat Tech and Acme Corp see DIFFERENT groups
- Fix user's original complaint about mock data

Let's do this! 🚀
