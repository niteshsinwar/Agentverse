# AgentVerse Cloud Backend

**Multi-Tenant Enterprise SaaS Backend**

## 🏢 **Architecture Overview**

This is the **cloud backend** for AgentVerse - a Microsoft Teams replacement with AI agents.

### **Purpose:**
- Multi-tenant data storage (PostgreSQL)
- Authentication & authorization (JWT)
- License enforcement (free vs paid)
- Real-time synchronization (WebSocket)
- Super admin portal (analytics, monitoring)

### **Tech Stack:**
- **Framework:** Django 5.0 + Django REST Framework
- **Database:** PostgreSQL (multi-tenant with django-tenants)
- **Vector DB:** Qdrant (self-hosted, free)
- **Storage:** MinIO (S3-compatible, free)
- **Real-Time:** Django Channels + Redis
- **Deployment:** Render

---

## 📊 **Data Model**

### **Multi-Tenant Hierarchy:**

```
Tenant (Organization)
├── Users (admin, normal users)
├── Groups (Teams/Channels)
│   ├── Group Members
│   ├── Messages (conversation history)
│   ├── Documents (uploaded files)
│   └── Agent Permissions (which agents visible)
├── Agents (created by admin)
├── Tools (created by admin)
└── MCP Servers (created by admin)
```

### **License Tiers:**

**Free Tier:**
- 3 users
- 2 groups
- 4 agents
- 7 tools
- 3 MCP servers

**Paid Tier:**
- Unlimited everything

---

## 🚀 **Setup**

### **1. Install Dependencies:**
```bash
cd cloud_backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### **2. Environment Variables:**
```bash
cp .env.example .env
# Edit .env with your PostgreSQL, Redis, MinIO credentials
```

### **3. Database Setup:**
```bash
python manage.py migrate_schemas --shared
python manage.py migrate
python manage.py createsuperuser  # For super admin portal
```

### **4. Run Development Server:**
```bash
# HTTP server
python manage.py runserver 0.0.0.0:9000

# WebSocket server (separate terminal)
daphne -b 0.0.0.0 -p 9001 agentverse_cloud.asgi:application
```

---

## 📁 **Project Structure**

```
cloud_backend/
├── agentverse_cloud/       # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   ├── tenants/           # Multi-tenancy management
│   ├── authentication/    # JWT auth, user management
│   ├── groups/            # Teams/channels
│   ├── agents/            # AI agents management
│   ├── tools/             # Custom tools
│   ├── mcp/              # MCP servers
│   ├── messages/          # Conversation history
│   ├── documents/         # File uploads
│   ├── permissions/       # Access control
│   ├── licenses/          # License enforcement
│   ├── realtime/          # WebSocket hub
│   └── superadmin/        # Super admin portal APIs
├── manage.py
├── requirements.txt
└── README.md
```

---

## 🔐 **Authentication Flow**

```
1. User logs in from desktop app
   POST /api/auth/login
   → Returns JWT token + user info

2. Desktop app stores token

3. All requests include token:
   Authorization: Bearer <token>

4. Local backend validates token with cloud:
   POST /api/auth/validate-token
   → Returns user permissions
```

---

## 🌐 **API Endpoints**

### **Authentication:**
- `POST /api/auth/register` - Register tenant
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - Logout
- `POST /api/auth/refresh` - Refresh token
- `POST /api/auth/validate-token` - Validate token (for local backend)

### **Tenants:**
- `GET /api/tenants/me` - Get current tenant info
- `PATCH /api/tenants/me` - Update tenant settings
- `GET /api/tenants/me/license` - Get license info

### **Users:**
- `GET /api/users` - List users (admin only)
- `POST /api/users` - Create user (admin only)
- `GET /api/users/:id` - Get user
- `PATCH /api/users/:id` - Update user
- `DELETE /api/users/:id` - Delete user (admin only)

### **Groups:**
- `GET /api/groups` - List groups
- `POST /api/groups` - Create group (admin only)
- `GET /api/groups/:id` - Get group
- `POST /api/groups/:id/members` - Add member
- `DELETE /api/groups/:id/members/:user_id` - Remove member

### **Agents:**
- `GET /api/agents` - List agents
- `POST /api/agents` - Create agent (admin only)
- `GET /api/agents/:id` - Get agent
- `PATCH /api/agents/:id` - Update agent (admin only)
- `DELETE /api/agents/:id` - Delete agent (admin only)
- `POST /api/agents/:id/groups/:group_id` - Assign to group (admin only)

### **Messages:**
- `GET /api/groups/:id/messages` - Get conversation history
- `POST /api/groups/:id/messages` - Send message
- `GET /api/messages/:id` - Get message

### **Documents:**
- `POST /api/groups/:id/documents` - Upload document
- `GET /api/groups/:id/documents` - List documents
- `GET /api/documents/:id` - Get document

### **Super Admin Portal:**
- `GET /api/superadmin/stats` - Overall stats
- `GET /api/superadmin/tenants` - List all tenants
- `GET /api/superadmin/health` - System health
- `GET /api/superadmin/analytics` - Usage analytics
- `GET /api/superadmin/tickets` - Support tickets

---

## 📡 **WebSocket Endpoints**

### **Group Collaboration:**
```
ws://localhost:9001/ws/groups/<group_id>/?token=<jwt>

Events:
- message.new - New message in group
- message.update - Message updated
- agent.typing - Agent is processing
- document.uploaded - New document
- user.joined - User joined group
- user.left - User left group
```

---

## 🧪 **Testing**

```bash
# Run all tests
pytest

# With coverage
pytest --cov=apps --cov-report=html

# Specific app
pytest apps/tenants/tests/
```

---

## 🚀 **Deployment (Render)**

### **1. Create Render Account**

### **2. Create PostgreSQL Database:**
- Render Dashboard → New → PostgreSQL
- Note: connection URL

### **3. Create Redis Instance:**
- Render Dashboard → New → Redis
- Note: connection URL

### **4. Create Web Service:**
- Render Dashboard → New → Web Service
- Connect GitHub repo
- Build command: `pip install -r cloud_backend/requirements.txt`
- Start command: `cd cloud_backend && gunicorn agentverse_cloud.wsgi:application`
- Environment variables:
  - `DATABASE_URL` - From step 2
  - `REDIS_URL` - From step 3
  - `SECRET_KEY` - Generate random string
  - `DEBUG` - False
  - `ALLOWED_HOSTS` - Your render domain

### **5. Create Background Worker (for WebSocket):**
- Render Dashboard → New → Background Worker
- Start command: `cd cloud_backend && daphne agentverse_cloud.asgi:application`

---

## 📊 **Super Admin Portal Metrics**

The super admin can view:

1. **Tenant Metrics:**
   - Total tenants (free vs paid)
   - New signups (daily/weekly/monthly)
   - Churn rate

2. **Usage Metrics:**
   - Active users (DAU/MAU)
   - Messages sent
   - Agents created
   - Storage used

3. **System Health:**
   - API response times
   - Database query performance
   - WebSocket connections
   - Error rates

4. **Support:**
   - Open tickets
   - Response times
   - Customer satisfaction

---

## 🔧 **Development Commands**

```bash
# Create new app
python manage.py startapp app_name apps/app_name

# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate_schemas  # For tenants

# Create superuser
python manage.py createsuperuser

# Run shell
python manage.py shell_plus  # With django-extensions

# Collect static files
python manage.py collectstatic

# Run tests
pytest
```

---

## 📝 **License**

Proprietary - AgentVerse Enterprise
