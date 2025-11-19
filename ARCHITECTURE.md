# AgentVerse Enterprise Architecture

**Microsoft Teams Replacement with AI Agents - Multi-Tenant SaaS**

---

## 🎯 **Product Vision**

AgentVerse is an enterprise collaboration platform where teams can:
- Chat in groups (like Microsoft Teams)
- Create custom AI agents
- Give agents access to tools and MCP servers
- Collaborate in real-time with AI assistance
- Manage everything from admin portal

**Key Differentiator:** AI agents you can create, configure, and collaborate with directly in your workflow.

---

## 🏗️ **System Architecture**

```
┌─────────────────────────────────────────────────────────────────────┐
│                   USER'S DESKTOP (Tauri App)                         │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  LOCAL FRONTEND (React - localhost:1420)                       │ │
│  │  - Login UI                                                     │ │
│  │  - Teams/Groups interface                                      │ │
│  │  - Real-time chat with agents                                  │ │
│  │  - Agent/Tool/MCP management (admin)                           │ │
│  └──────┬─────────────────────────────────────────────────────────┘ │
│         │                                                             │
│         │ HTTP/WebSocket                                             │
│         ↓                                                             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  LOCAL BACKEND (FastAPI - localhost:8000)                     │ │
│  │                                                                 │ │
│  │  EXECUTES (requires local file system):                       │ │
│  │  ✅ AI agents (LLM calls)                                     │ │
│  │  ✅ MCP servers (local processes - file system, etc.)         │ │
│  │  ✅ Tools execution (file operations, shell commands)         │ │
│  │  ✅ Document processing (OCR, vision, extraction)            │ │
│  │                                                                 │ │
│  │  STORES NOTHING - All data goes to cloud                      │ │
│  └──────┬──────────────────────────────────────────────────────────┘ │
└─────────┼────────────────────────────────────────────────────────────┘
          │
          │ HTTPS + JWT Token
          ↓
┌─────────────────────────────────────────────────────────────────────┐
│              CLOUD BACKEND (Django - Render.com)                     │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  CLOUD API (Django REST Framework)                            │ │
│  │  - Multi-tenant authentication                                 │ │
│  │  - Permission enforcement (admin vs user)                      │ │
│  │  - License validation (free vs paid)                           │ │
│  │  - Real-time WebSocket hub                                     │ │
│  │  - REST APIs for all data operations                           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  DATABASE (PostgreSQL)                                         │ │
│  │                                                                 │ │
│  │  TENANT SCOPE:                                                 │ │
│  │  - tenants (organizations)                                     │ │
│  │  - users (with roles: admin, user)                            │ │
│  │  - agents (AI agents created by admin)                        │ │
│  │  - tools (custom Python tools)                                │ │
│  │  - mcp_servers (MCP configurations)                           │ │
│  │  - groups (teams/channels)                                     │ │
│  │  - licenses (free/paid tiers)                                 │ │
│  │                                                                 │ │
│  │  TENANT + GROUP SCOPE:                                         │ │
│  │  - messages (conversation history)                             │ │
│  │  - documents (uploaded files metadata)                        │ │
│  │  - group_members (user assignments)                           │ │
│  │  - agent_permissions (agent visibility in groups)             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  VECTOR DATABASE (Qdrant - Self-Hosted)                       │ │
│  │  - Document embeddings for RAG                                 │ │
│  │  - Collections per tenant + group                              │ │
│  │  - Namespace: {tenant_id}_{group_id}                          │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  OBJECT STORAGE (MinIO - Self-Hosted S3)                      │ │
│  │  - Uploaded documents (original files)                         │ │
│  │  - Agent avatars/icons                                         │ │
│  │  - Path: /{tenant_id}/{group_id}/{file_id}                   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  CACHE (Redis)                                                 │ │
│  │  - Session data                                                │ │
│  │  - Permission cache                                            │ │
│  │  - WebSocket connections                                       │ │
│  │  - Rate limiting counters                                      │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│         SUPER ADMIN PORTAL (React - admin.agentverse.com)           │
│                                                                       │
│  CLOUD FRONTEND - For Platform Administrators Only                  │
│                                                                       │
│  - Tenant management (all organizations)                             │
│  - System health monitoring                                          │
│  - Usage analytics & graphs                                          │
│  - Support ticket management                                         │
│  - Subscription billing                                              │
│  - Error tracking                                                    │
│  - Free vs Paid tenant metrics                                       │
│                                                                       │
│  CANNOT SEE: Tenant-specific data (messages, documents, etc.)       │
│  CAN SEE: Metadata, metrics, health, billing                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📊 **Multi-Tenant Data Model**

### **Tenant Hierarchy:**

```sql
-- TENANT (Organization)
tenants
├── id (uuid, primary key)
├── name (string) -- "Acme Corporation"
├── slug (string, unique) -- "acme-corp"
├── license_type (enum: free, paid)
├── license_limits (jsonb) -- {users: 3, groups: 2, agents: 4...}
├── subscription_status (enum: active, suspended, cancelled)
├── created_at, updated_at

-- USERS (People in organization)
users
├── id (uuid)
├── tenant_id (fk → tenants)
├── email (string, unique within tenant)
├── password_hash (string)
├── role (enum: admin, user)
├── is_active (boolean)
├── last_login (timestamp)
├── created_at, updated_at

-- GROUPS (Teams/Channels within tenant)
groups
├── id (uuid)
├── tenant_id (fk → tenants)
├── name (string) -- "#marketing", "#engineering"
├── description (text)
├── is_private (boolean)
├── created_by (fk → users, admin)
├── created_at, updated_at

-- GROUP MEMBERS (Which users in which groups)
group_members
├── id (uuid)
├── group_id (fk → groups)
├── user_id (fk → users)
├── role (enum: member, moderator)
├── joined_at

-- AGENTS (AI agents created by admin)
agents
├── id (uuid)
├── tenant_id (fk → tenants)
├── name (string) -- "sales_agent"
├── display_name (string) -- "Sales Assistant"
├── description (text)
├── emoji (string) -- "💼"
├── system_prompt (text)
├── llm_provider (enum: openai, anthropic, gemini)
├── llm_model (string) -- "gpt-4"
├── temperature (float)
├── config (jsonb) -- Additional settings
├── created_by (fk → users, admin)
├── created_at, updated_at

-- AGENT GROUP PERMISSIONS (Which agents visible in which groups)
agent_group_permissions
├── id (uuid)
├── agent_id (fk → agents)
├── group_id (fk → groups)
├── granted_by (fk → users, admin)
├── granted_at

-- TOOLS (Custom Python tools)
tools
├── id (uuid)
├── tenant_id (fk → tenants)
├── name (string) -- "calculate_roi"
├── description (text)
├── code (text) -- Python code
├── dependencies (jsonb) -- ["numpy>=1.24.0"]
├── is_active (boolean)
├── created_by (fk → users, admin)
├── created_at, updated_at

-- MCP SERVERS (MCP configurations)
mcp_servers
├── id (uuid)
├── tenant_id (fk → tenants)
├── name (string) -- "filesystem"
├── description (text)
├── command (string) -- "npx"
├── args (jsonb) -- ["@modelcontextprotocol/server-filesystem"]
├── env (jsonb) -- Environment variables
├── requires_auth (boolean)
├── created_by (fk → users, admin)
├── created_at, updated_at

-- MESSAGES (Conversation history)
messages
├── id (uuid)
├── group_id (fk → groups)
├── tenant_id (fk → tenants)
├── sender_type (enum: user, agent, system)
├── sender_id (uuid) -- user_id or agent_id
├── content (text)
├── role (enum: user, agent, system, tool_call, tool_result)
├── metadata (jsonb)
├── parent_id (fk → messages, nullable) -- For threads
├── created_at

-- DOCUMENTS (Uploaded files)
documents
├── id (uuid)
├── group_id (fk → groups)
├── tenant_id (fk → tenants)
├── uploaded_by (fk → users)
├── filename (string)
├── file_size (bigint) -- bytes
├── mime_type (string)
├── storage_path (string) -- MinIO path
├── extracted_text (text)
├── metadata (jsonb)
├── created_at

-- LICENSES (Subscription management)
licenses
├── id (uuid)
├── tenant_id (fk → tenants)
├── type (enum: free, paid)
├── limits (jsonb) -- {users: 3, groups: 2...}
├── current_usage (jsonb) -- {users: 1, groups: 1...}
├── billing_cycle (enum: monthly, annual)
├── amount (decimal)
├── currency (string)
├── stripe_subscription_id (string, nullable)
├── valid_from, valid_until
```

---

## 🔐 **Authentication & Authorization**

### **1. Login Flow:**

```
User opens desktop app
  ↓
1. Enter email + password
  ↓
2. Desktop → Cloud: POST /api/auth/login
   {
     "email": "john@acme.com",
     "password": "***"
   }
  ↓
3. Cloud validates credentials
  ↓
4. Cloud returns JWT + user info
   {
     "access_token": "eyJhbGc...",
     "refresh_token": "eyJhbGc...",
     "user": {
       "id": "uuid",
       "email": "john@acme.com",
       "tenant_id": "acme-corp-uuid",
       "role": "admin" | "user",
       "permissions": {
         "can_create_agent": true,
         "can_create_tool": true,
         ...
       }
     }
   }
  ↓
5. Desktop stores tokens in secure storage
  ↓
6. Desktop connects to local backend
   Local backend validates token with cloud
  ↓
7. User can now interact with system
```

### **2. Permission System:**

```python
# Admin permissions
ADMIN_PERMISSIONS = [
    "agent.create",
    "agent.update",
    "agent.delete",
    "agent.assign_to_group",
    "tool.create",
    "tool.update",
    "tool.delete",
    "mcp.create",
    "mcp.update",
    "mcp.delete",
    "group.create",
    "group.update",
    "group.delete",
    "user.invite",
    "user.remove",
    "user.set_permissions",
]

# Normal user permissions
USER_PERMISSIONS = [
    "agent.view",          # Only agents in their groups
    "agent.chat",          # Send messages to agents
    "message.send",        # Send messages in groups
    "message.view",        # View group conversations
    "document.upload",     # Upload documents to groups
    "document.view",       # View documents in groups
]

# Permission check example
def check_permission(user, permission, resource=None):
    if user.role == "admin":
        return True

    if permission in USER_PERMISSIONS:
        # Additional checks for resource access
        if resource and resource.group_id:
            return user.is_member_of_group(resource.group_id)
        return True

    return False
```

---

## 📋 **License Enforcement**

### **Free Tier Limits:**
```python
FREE_TIER = {
    "max_users": 3,
    "max_groups": 2,
    "max_agents": 4,
    "max_tools": 7,
    "max_mcp": 3,
    "max_storage_mb": 100,
    "max_messages_per_month": 1000,
}
```

### **Paid Tier:**
```python
PAID_TIER = {
    "max_users": float('inf'),  # Unlimited
    "max_groups": float('inf'),
    "max_agents": float('inf'),
    "max_tools": float('inf'),
    "max_mcp": float('inf'),
    "max_storage_mb": float('inf'),
    "max_messages_per_month": float('inf'),
}
```

### **Enforcement Points:**

```python
# Before creating resource
@license_enforcer.check_limit("max_users")
def create_user(tenant_id, user_data):
    # Only executes if within limits
    pass

# If limit exceeded:
raise LicenseError(
    message="User limit reached",
    current=3,
    max=3,
    upgrade_url="/pricing"
)
```

---

## 🔄 **Real-Time Collaboration**

### **WebSocket Flow:**

```
1. User logs in
   Desktop connects to: ws://cloud.agentverse.com/ws/groups/{group_id}/?token={jwt}

2. Cloud validates token and group membership

3. User sends message in group
   Desktop → Local backend → Execute agent
   Local backend → Cloud: POST /api/groups/{id}/messages

4. Cloud saves message and broadcasts:
   {
     "type": "message.new",
     "group_id": "uuid",
     "message": {
       "id": "uuid",
       "sender": "user_id",
       "content": "Hello agent!",
       "timestamp": "2024-01-01T12:00:00Z"
     }
   }

5. All connected users in group receive update instantly

6. Agent processes message (local backend)
   Local backend → Cloud: POST /api/groups/{id}/messages (agent response)

7. Cloud broadcasts agent response:
   {
     "type": "message.new",
     "group_id": "uuid",
     "message": {
       "id": "uuid",
       "sender": "agent_id",
       "content": "Hello! How can I help?",
       "timestamp": "2024-01-01T12:00:02Z"
     }
   }

8. All users see agent response in real-time
```

---

## 🎛️ **Super Admin Portal**

### **Purpose:**
Platform administrators (not tenant users) can monitor and manage the entire system.

### **Features:**

**1. Dashboard:**
- Total tenants (free vs paid)
- Active users (DAU/MAU)
- Revenue (MRR, ARR)
- System health

**2. Tenant Management:**
```
List View:
- Tenant name
- License type
- Users count
- Created date
- Last activity
- Actions: View details, Suspend, Cancel

Detail View:
- Tenant info (cannot see messages/documents)
- License usage vs limits
- User list (names/emails only)
- Billing history
- Support tickets
```

**3. Analytics:**
```
Graphs:
- New signups over time
- Churn rate
- Feature adoption
- API usage
- Storage usage
- LLM API costs
```

**4. System Health:**
```
Metrics:
- API response times (p50, p95, p99)
- Database query performance
- WebSocket connections
- Error rates (by endpoint)
- Background job queue
```

**5. Support Tickets:**
```
- Ticket ID
- Tenant name
- User email
- Issue type
- Priority
- Status
- Assigned to
- Created date
```

---

## 🚀 **Deployment Architecture (Render)**

```
┌─────────────────────────────────────────┐
│  Render.com                              │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  Web Service (Django)              │ │
│  │  - Public URL: api.agentverse.com  │ │
│  │  - Instances: Auto-scaling         │ │
│  │  - Start: gunicorn                 │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  Background Worker (WebSocket)     │ │
│  │  - Start: daphne                   │ │
│  │  - Instances: 2+                   │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  PostgreSQL (Managed)              │ │
│  │  - Plan: Standard+                 │ │
│  │  - Backups: Daily                  │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  Redis (Managed)                   │ │
│  │  - For: WebSocket, Cache           │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Self-Hosted (VPS or Render)            │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  Qdrant (Vector DB)                │ │
│  │  - Docker container                │ │
│  │  - Port: 6333                      │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  MinIO (Object Storage)            │ │
│  │  - Docker container                │ │
│  │  - S3-compatible API               │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

## 📁 **Project Structure**

```
agentverse/
│
├── local_backend/              # FastAPI (execution engine)
│   ├── src/
│   │   ├── core/
│   │   │   ├── agents/        # Agent execution
│   │   │   ├── tools/         # Tool execution
│   │   │   ├── mcp/           # MCP server management
│   │   │   └── document_processing/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── execute.py # Execute agents/tools
│   │   │       └── validate.py # Validate with cloud
│   │   └── middleware/
│   │       └── auth.py        # JWT validation
│   └── requirements.txt
│
├── local_frontend/             # React (Tauri desktop app)
│   ├── src/
│   │   ├── api/
│   │   │   ├── cloud.ts       # Cloud API calls
│   │   │   └── local.ts       # Local API calls
│   │   ├── components/
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Groups.tsx
│   │   │   ├── Chat.tsx
│   │   │   └── AdminPanel.tsx
│   │   └── contexts/
│   └── package.json
│
├── cloud_backend/              # Django (multi-tenant SaaS)
│   ├── agentverse_cloud/      # Project settings
│   ├── apps/
│   │   ├── tenants/           # Multi-tenancy
│   │   ├── authentication/    # JWT auth
│   │   ├── users/
│   │   ├── groups/
│   │   ├── agents/
│   │   ├── tools/
│   │   ├── mcp/
│   │   ├── messages/
│   │   ├── documents/
│   │   ├── permissions/
│   │   ├── licenses/
│   │   ├── realtime/          # WebSocket
│   │   └── superadmin/        # Super admin APIs
│   ├── manage.py
│   └── requirements.txt
│
└── cloud_frontend/             # React (super admin portal)
    ├── src/
    │   ├── pages/
    │   │   ├── Dashboard.tsx
    │   │   ├── Tenants.tsx
    │   │   ├── Analytics.tsx
    │   │   ├── Health.tsx
    │   │   └── Tickets.tsx
    │   └── api/
    │       └── superadmin.ts
    └── package.json
```

---

## 🎯 **User Flows**

### **1. Admin Creates Agent:**

```
1. Admin logs into desktop app
2. Opens Admin Panel
3. Clicks "Create Agent"
4. Fills form:
   - Name: "sales_agent"
   - Description: "Helps with sales inquiries"
   - LLM: GPT-4
   - Tools: [calculate_roi, get_pricing]
   - MCP: [salesforce]
5. Clicks "Create"
6. Local frontend → Cloud backend: POST /api/agents
7. Cloud:
   - Validates admin permission
   - Checks license limit (free: max 4 agents)
   - Creates agent in database
   - Broadcasts to all admins via WebSocket
8. Agent appears in admin's agent list
9. Admin assigns agent to #sales group
10. Local → Cloud: POST /api/agents/{id}/groups/{group_id}
11. All users in #sales group see new agent available
```

### **2. User Chats with Agent:**

```
1. User opens #sales group
2. Types: "@sales_agent What's our pricing for Enterprise?"
3. Local frontend → Local backend: POST /api/execute/agent
4. Local backend:
   - Validates user has access to group
   - Loads agent config from cloud
   - Executes agent (LLM call, tool calls)
   - Sends message + response to cloud
5. Cloud:
   - Saves user message
   - Saves agent response
   - Broadcasts both to all group members via WebSocket
6. All users in #sales see:
   - User's question
   - Agent's response (with pricing info)
```

### **3. Super Admin Monitors System:**

```
1. Super admin opens admin.agentverse.com
2. Sees dashboard:
   - 50 tenants (30 free, 20 paid)
   - 500 active users
   - 10,000 messages/day
   - $5,000 MRR
3. Clicks "Tenants" tab
4. Sees list of all organizations:
   - Acme Corp (paid, 25 users, healthy)
   - Beta Inc (free, 2 users, low activity)
5. Clicks on Acme Corp
6. Sees:
   - License: Paid ($99/mo)
   - Users: 25/unlimited
   - Groups: 10
   - Agents: 15
   - Last activity: 5 minutes ago
   - Support tickets: 0 open
7. Cannot see: Their messages, documents, or conversation content
```

---

## 🔧 **Development Workflow**

### **Local Development:**

```bash
# Terminal 1: Cloud backend
cd cloud_backend
python manage.py runserver 9000

# Terminal 2: Cloud WebSocket
cd cloud_backend
daphne -p 9001 agentverse_cloud.asgi:application

# Terminal 3: Local backend
cd local_backend
python server.py  # Port 8000

# Terminal 4: Local frontend
cd local_frontend
npm run dev  # Port 1420
```

### **Testing Multi-Tenancy:**

```bash
# Create test tenants
python manage.py create_test_tenants

# Creates:
# - Tenant A (free): 2 users, 1 group, 2 agents
# - Tenant B (paid): 10 users, 5 groups, 10 agents

# Test isolation:
# - User from Tenant A cannot see Tenant B's data
# - Agents from Tenant A not visible to Tenant B
```

---

## 📊 **Scaling Considerations**

### **Current (MVP):**
- 100 tenants
- 1,000 users
- 10,000 messages/day

### **Scale to (Year 1):**
- 1,000 tenants
- 10,000 users
- 100,000 messages/day

### **Optimizations Needed:**

1. **Database:**
   - Connection pooling
   - Read replicas
   - Query optimization
   - Indexing

2. **WebSocket:**
   - Redis pub/sub for horizontal scaling
   - Sticky sessions
   - Load balancing

3. **Storage:**
   - CDN for uploaded files
   - Image optimization
   - Lazy loading

4. **Caching:**
   - Redis for frequent queries
   - Permission caching
   - Agent config caching

---

**END OF ARCHITECTURE DOCUMENT**

Next steps: Implement cloud_backend Django apps
