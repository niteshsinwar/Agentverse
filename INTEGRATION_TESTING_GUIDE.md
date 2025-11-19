# AgentVerse Integration Testing Guide

Complete guide for testing the integrated multi-tenant system with all four components.

## Overview

This guide covers end-to-end testing of the complete AgentVerse architecture:

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Local Frontend │─────▶│  Local Backend  │─────▶│  Cloud Backend  │
│  (React/Vite)   │      │  (FastAPI:8000) │      │  (Django:9000)  │
│  Port: 5173     │      │  + WebSocket    │      │  + WebSocket    │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                                            │
                                                            ▼
                                                   ┌─────────────────┐
                                                   │ Cloud Frontend  │
                                                   │ (Django Admin)  │
                                                   │ Port: 9000/admin│
                                                   └─────────────────┘
```

## Prerequisites

### System Requirements
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+ (optional, can use SQLite)
- Redis (optional for production WebSocket)

### Environment Setup

1. **Clone Repository**
```bash
git clone <repository_url>
cd Agentverse
```

2. **Install Python Dependencies**
```bash
# Cloud Backend
cd cloud_backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Local Backend
cd ../local_backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Install Node Dependencies**
```bash
# Local Frontend
cd local_frontend
npm install
```

## Testing Modes

### Mode 1: SQLite (Quick Testing)
**Use Case:** Development, testing, no PostgreSQL needed

**Advantages:**
- No database setup required
- Fast startup
- Easy reset (delete db.sqlite3)
- Single tenant mode

**Limitations:**
- No true multi-tenancy
- Single tenant only
- Not production-ready

### Mode 2: PostgreSQL (Production Testing)
**Use Case:** Full multi-tenant testing, production simulation

**Advantages:**
- True multi-tenancy with schema isolation
- Multiple tenants
- Production-like environment
- Domain-based routing

**Limitations:**
- Requires PostgreSQL setup
- More complex configuration

## Quick Start: SQLite Mode

This is the fastest way to test the complete system.

### Step 1: Start Cloud Backend (SQLite)

```bash
cd cloud_backend

# Set environment variables
export DATABASE_URL="sqlite:///./db.sqlite3"
export DJANGO_SECRET_KEY="test-secret-key-change-in-production"
export DEBUG="True"

# Run migrations
python manage.py migrate

# Create superuser for admin
python manage.py createsuperuser
# Email: admin@example.com
# Password: admin123

# Start server
python manage.py runserver 0.0.0.0:9000
```

**Verify:** Open http://localhost:9000/admin/ and login

### Step 2: Start Local Backend

```bash
cd local_backend

# Set environment variables
export CLOUD_ENABLED="true"
export CLOUD_BASE_URL="http://localhost:9000"
export OPENAI_API_KEY="your-openai-api-key"

# Start server
python server.py
```

**Expected Output:**
```
🚀 Backend Server: Starting up...
🔍 Running comprehensive startup validation...
✅ Startup validation passed
☁️  Cloud integration enabled - initializing...
✅ Cloud client initialized: http://localhost:9000
✅ Local cache initialized: .agentverse/cache
⚠️  No cloud token - skipping data sync (login required)
✅ Backend Server: Initialized with 0 agents
```

**Verify:** Open http://localhost:8000/docs

### Step 3: Get Cloud Token

You need a JWT token to authenticate local backend with cloud.

**Option A: Using Django Admin**
1. Go to http://localhost:9000/admin/
2. Login with superuser credentials
3. Use browser dev tools to get token from API call

**Option B: Using API (Recommended)**
```bash
curl -X POST http://localhost:9000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

Copy the `access` token.

### Step 4: Restart Local Backend with Token

```bash
cd local_backend

# Stop the server (Ctrl+C)

# Set token
export CLOUD_TOKEN="<paste_access_token_here>"

# Restart
python server.py
```

**Expected Output:**
```
🔄 Syncing tenant data from cloud...
✅ Cloud data synced successfully
🔌 Connecting to cloud WebSocket for real-time sync...
✅ Cloud WebSocket connected - real-time sync enabled
```

### Step 5: Start Local Frontend

```bash
cd local_frontend

# Start dev server
npm run dev
```

**Verify:** Open http://localhost:5173

### Step 6: Test Real-Time Sync

**Test WebSocket synchronization:**

1. **In Cloud Admin** (http://localhost:9000/admin/):
   - Go to "Agents" → "Add Agent"
   - Create a new agent:
     - Name: "Test Agent"
     - Emoji: 🤖
     - LLM Provider: OpenAI
     - LLM Model: gpt-4o
     - System Prompt: "You are a helpful assistant"
   - Click "Save"

2. **Check Local Backend Logs:**
   ```
   📥 Received sync event: agent_updated
   Updating agent cache: Test Agent (<agent_id>)
   ✅ Agent cache updated: Test Agent
   ```

3. **Verify in Local Backend API:**
   ```bash
   curl http://localhost:8000/api/v1/agents/
   ```

   Should return the newly created agent.

**This confirms real-time sync is working!** 🎉

## Complete Integration Test

### Test 1: Agent CRUD via Cloud

```bash
# Create Agent
curl -X POST http://localhost:9000/api/v1/agents/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customer Support Bot",
    "emoji": "👨‍💼",
    "llm_provider": "openai",
    "llm_model": "gpt-4o",
    "system_prompt": "You are a customer support agent.",
    "config": {"temperature": 0.7}
  }'

# List Agents
curl http://localhost:8000/api/v1/agents/

# Update Agent
curl -X PUT http://localhost:9000/api/v1/agents/<agent_id>/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customer Support Bot v2",
    "system_prompt": "You are an expert customer support agent."
  }'

# Check local backend logs for sync event
# Verify cache was updated
curl http://localhost:8000/api/v1/agents/<agent_id>/
```

### Test 2: Tool CRUD via Cloud

```bash
# Create Tool
curl -X POST http://localhost:9000/api/v1/tools/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_weather",
    "description": "Get current weather for a location",
    "tool_type": "function",
    "code": "def get_weather(location: str) -> str:\\n    return f\"Weather in {location}: 72°F, Sunny\""
  }'

# Verify local backend received sync
curl http://localhost:8000/api/v1/tools/
```

### Test 3: MCP Server Configuration

```bash
# Create MCP Server
curl -X POST http://localhost:9000/api/v1/mcp-servers/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "File System Server",
    "command": "npx",
    "args": ["@modelcontextprotocol/server-filesystem", "/tmp"],
    "env": {}
  }'

# Verify sync
curl http://localhost:8000/api/v1/mcp-servers/
```

### Test 4: Group & Message Management

```bash
# Create Group
curl -X POST http://localhost:9000/api/v1/groups/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customer Support",
    "description": "Customer support conversations",
    "members": [],
    "assigned_agents": ["<agent_id>"]
  }'

# Create Message
curl -X POST http://localhost:9000/api/v1/groups/<group_id>/messages/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sender_type": "user",
    "sender_id": "<user_id>",
    "content": "Hello, I need help!"
  }'
```

### Test 5: WebSocket Chat (Real-Time Messages)

**Using JavaScript in Browser Console:**

```javascript
// Connect to message WebSocket
const token = '<your_jwt_token>';
const groupId = '<group_id>';
const ws = new WebSocket(`ws://localhost:9000/ws/messages/${groupId}/?token=${token}`);

ws.onopen = () => console.log('✅ Connected to chat');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('📥 Received:', data);
};

// Send typing indicator
ws.send(JSON.stringify({
  type: 'typing_indicator',
  is_typing: true
}));

// Create a message via API in another terminal
// Watch it appear in WebSocket
```

### Test 6: WebSocket Sync (Real-Time Config Updates)

**Using JavaScript:**

```javascript
const token = '<your_jwt_token>';
const ws = new WebSocket(`ws://localhost:9000/ws/sync/?token=${token}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('🔄 Config update:', data);
  // Update local cache based on event type
};

// Now update an agent in Django Admin
// Watch the sync event appear here immediately
```

## Advanced Testing: PostgreSQL Mode

### Setup PostgreSQL

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb agentverse

# Create user
sudo -u postgres psql
postgres=# CREATE USER agentverse WITH PASSWORD 'password123';
postgres=# GRANT ALL PRIVILEGES ON DATABASE agentverse TO agentverse;
postgres=# \q
```

### Configure Cloud Backend for PostgreSQL

```bash
cd cloud_backend

# Update .env
cat > .env << EOF
DATABASE_URL=postgresql://agentverse:password123@localhost/agentverse
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
EOF

# Run multi-tenant migrations
python manage.py migrate_schemas --shared
python manage.py migrate_schemas

# Create superuser
python manage.py createsuperuser

# Start server
python manage.py runserver 0.0.0.0:9000
```

### Create Tenants

```bash
# Create tenant via Django shell
python manage.py shell << EOF
from apps.tenants.models import Tenant, Domain

# Create tenant
tenant = Tenant.objects.create(
    schema_name='acme',
    name='ACME Corporation',
    slug='acme',
    email='admin@acme.com',
    license_type='pro'
)

# Create domain
Domain.objects.create(
    domain='acme.localhost',
    tenant=tenant,
    is_primary=True
)

print(f"✅ Created tenant: {tenant.name}")
print(f"   Schema: {tenant.schema_name}")
print(f"   Domain: acme.localhost")
EOF
```

### Test Multi-Tenant Isolation

```bash
# Access tenant 1
curl http://acme.localhost:9000/api/v1/agents/ \
  -H "Host: acme.localhost"

# Access tenant 2 (should see different data)
curl http://techco.localhost:9000/api/v1/agents/ \
  -H "Host: techco.localhost"
```

## Troubleshooting

### Issue: WebSocket Connection Fails

**Symptoms:**
```
❌ WebSocket connection failed: [Errno 111] Connection refused
```

**Solutions:**
1. Verify cloud backend is running on port 9000
2. Check WebSocket URL format: `ws://localhost:9000/ws/sync/?token=<jwt>`
3. Verify JWT token is valid
4. Check firewall settings

### Issue: No Sync Events Received

**Symptoms:**
- Agent created in cloud admin
- No sync event in local backend logs

**Solutions:**
1. Check WebSocket connection status: `get_cloud_websocket().is_connected()`
2. Verify Django signals are registered (check apps.py has `ready()` method)
3. Check Redis is running (production mode)
4. Verify channel layer configuration in settings.py

### Issue: 401 Unauthorized

**Symptoms:**
```
401 Unauthorized: Invalid or expired token
```

**Solutions:**
1. Token expired - get new token via login API
2. Check token is being sent in Authorization header
3. Verify SECRET_KEY matches between token generation and validation

### Issue: Agent Execution Fails

**Symptoms:**
```
Agent not found in cache
```

**Solutions:**
1. Verify cloud sync completed: check local backend startup logs
2. Force sync: restart local backend with CLOUD_TOKEN
3. Check cache database: `.agentverse/cache/cloud_data.db`

## Performance Testing

### Load Test: Concurrent Agent Executions

```bash
# Install locust
pip install locust

# Create locustfile.py
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class AgentUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def execute_agent(self):
        self.client.post("/api/v1/agents/<agent_id>/execute", json={
            "messages": [{"role": "user", "content": "Hello"}]
        })
EOF

# Run load test
locust -f locustfile.py --host http://localhost:8000
```

Open http://localhost:8089 and start test with:
- Number of users: 100
- Spawn rate: 10

### WebSocket Connection Test

```bash
# Test multiple WebSocket connections
for i in {1..100}; do
  node -e "
    const WebSocket = require('ws');
    const ws = new WebSocket('ws://localhost:9000/ws/sync/?token=<token>');
    ws.on('open', () => console.log('Connection $i: ✅'));
    ws.on('error', (err) => console.log('Connection $i: ❌', err));
  " &
done
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_DB: agentverse_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          cd cloud_backend
          pip install -r requirements.txt
          cd ../local_backend
          pip install -r requirements.txt

      - name: Run migrations
        run: |
          cd cloud_backend
          export DATABASE_URL="postgresql://test:test@localhost/agentverse_test"
          python manage.py migrate

      - name: Run tests
        run: |
          cd cloud_backend
          pytest
          cd ../local_backend
          pytest

      - name: Integration test
        run: |
          # Start cloud backend
          cd cloud_backend
          python manage.py runserver 9000 &

          # Wait for startup
          sleep 10

          # Start local backend
          cd ../local_backend
          export CLOUD_ENABLED=true
          export CLOUD_BASE_URL="http://localhost:9000"
          python server.py &

          # Run integration tests
          pytest tests/integration/
```

## Next Steps

1. ✅ Test all four modules independently
2. ✅ Test cloud backend WebSocket
3. ✅ Test local backend WebSocket sync
4. ⏸️ Update local frontend to use cloud APIs
5. ⏸️ End-to-end frontend→local→cloud test
6. ⏸️ Performance benchmarking
7. ⏸️ Deploy to staging environment

## Resources

- [Cloud Backend API Docs](http://localhost:9000/docs)
- [Local Backend API Docs](http://localhost:8000/docs)
- [Django Admin](http://localhost:9000/admin/)
- [Frontend](http://localhost:5173)

## Summary

This guide provides comprehensive testing procedures for the complete AgentVerse system. Start with SQLite mode for quick testing, then move to PostgreSQL for production-like multi-tenant testing.

**Testing Checklist:**
- [ ] Cloud backend runs (SQLite mode)
- [ ] Cloud backend runs (PostgreSQL mode)
- [ ] Local backend runs
- [ ] Local backend syncs from cloud
- [ ] WebSocket connection established
- [ ] Real-time sync works (agent/tool/MCP updates)
- [ ] Local frontend connects to local backend
- [ ] CRUD operations work via cloud API
- [ ] Agent execution uses cached configs
- [ ] Multi-tenant isolation verified
- [ ] Performance acceptable (>100 req/s)
