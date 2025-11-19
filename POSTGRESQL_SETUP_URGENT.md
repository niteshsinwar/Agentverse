# 🚨 URGENT: PostgreSQL Setup for Multi-Tenancy

## ⚠️ CRITICAL: Multi-Tenancy Requires PostgreSQL

You're absolutely right - **multi-tenancy is the most crucial part** of AgentVerse!

**Current Problem:**
- ❌ You're using SQLite
- ❌ SQLite does NOT support multi-tenancy
- ❌ `tenants_tenant` table cannot be created in SQLite
- ❌ Django-tenants requires PostgreSQL

**Solution:**
- ✅ Install PostgreSQL
- ✅ Configure cloud backend to use PostgreSQL
- ✅ Run migrations with PostgreSQL
- ✅ Multi-tenancy will work perfectly

---

## 🔥 IMMEDIATE SETUP GUIDE

### Step 1: Install PostgreSQL (2 minutes)

**On macOS (you're on Mac):**

```bash
# Install PostgreSQL
brew install postgresql@14

# Start PostgreSQL service
brew services start postgresql@14

# Verify it's running
brew services list | grep postgresql
# Should show: postgresql@14 started
```

**Verify Installation:**
```bash
psql --version
# Expected: psql (PostgreSQL) 14.x
```

---

### Step 2: Create Database (1 minute)

```bash
# Create the database
createdb agentverse_cloud

# Verify it was created
psql -l | grep agentverse
# Should show: agentverse_cloud

# Optional: Create a dedicated user
psql postgres
```

In psql:
```sql
CREATE USER agentverse WITH PASSWORD 'secure_password_here';
ALTER ROLE agentverse SET client_encoding TO 'utf8';
ALTER ROLE agentverse SET default_transaction_isolation TO 'read committed';
ALTER ROLE agentverse SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE agentverse_cloud TO agentverse;
\q
```

---

### Step 3: Update Cloud Backend Configuration (2 minutes)

**Create/Update `.env` file:**

```bash
cd cloud_backend

# Create .env file
cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://localhost/agentverse_cloud
# Or with custom user:
# DATABASE_URL=postgresql://agentverse:secure_password_here@localhost/agentverse_cloud

# Disable SQLite mode
USE_SQLITE=False

# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:8000,http://localhost:1420

# Redis (optional for now, can use InMemory)
# REDIS_URL=redis://localhost:6379/0
# CELERY_BROKER_URL=redis://localhost:6379/1
EOF
```

**Verify Configuration:**
```bash
cat .env | grep DATABASE_URL
# Should show: DATABASE_URL=postgresql://localhost/agentverse_cloud
```

---

### Step 4: Install PostgreSQL Python Package (1 minute)

```bash
cd cloud_backend

# Make sure you're in virtual environment
source venv/bin/activate

# Install psycopg2 (PostgreSQL adapter for Python)
pip install psycopg2-binary

# Verify installation
pip list | grep psycopg2
# Should show: psycopg2-binary
```

---

### Step 5: Run Migrations with PostgreSQL (2 minutes)

```bash
cd cloud_backend

# Clear any old SQLite database (optional)
rm -f db.sqlite3

# Run migrations
python manage.py migrate

# Expected output:
# Operations to perform:
#   Apply all migrations: admin, auth, contenttypes, sessions, tenants, ...
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   Applying contenttypes.0002_remove_content_type_name... OK
#   Applying auth.0001_initial... OK
#   ...
#   Applying tenants.0001_initial... OK  ← TENANTS CREATED!
#   Applying tenants.0002_auto_... OK
#   ...
# ✅ All migrations applied
```

**Verify Tables Created:**
```bash
psql agentverse_cloud -c "\dt" | grep tenants
# Should show:
# tenants_tenant
# tenants_domain
# tenants_tenantinvitation
# ✅ TENANT TABLES EXIST!
```

---

### Step 6: Create Public Tenant (CRITICAL - 3 minutes)

**Django-tenants requires a "public" tenant for shared data.**

```bash
cd cloud_backend
python manage.py shell
```

In the Django shell:
```python
from apps.tenants.models import Tenant, Domain

# Check if public tenant already exists
if Tenant.objects.filter(schema_name='public').exists():
    print("✅ Public tenant already exists")
else:
    # Create public tenant
    public_tenant = Tenant.objects.create(
        schema_name='public',
        name='Public Schema',
        slug='public',
        license_type='free',
        subscription_status='active',
        is_active=True
    )
    print(f"✅ Created public tenant: {public_tenant}")

    # Create domain for public tenant
    domain = Domain.objects.create(
        domain='localhost',  # Your domain
        tenant=public_tenant,
        is_primary=True
    )
    print(f"✅ Created domain: {domain}")

print("\n🎉 Public tenant setup complete!")
exit()
```

---

### Step 7: Create Your First Real Tenant (2 minutes)

```bash
python manage.py shell
```

In the Django shell:
```python
from apps.tenants.models import Tenant, Domain

# Create your first tenant (e.g., for "Acme Inc")
tenant = Tenant.objects.create(
    schema_name='tenant_acme',  # PostgreSQL schema name (no special chars except underscore)
    name='Acme Inc',
    slug='acme',
    license_type='professional',  # or 'free', 'enterprise'
    subscription_status='active',
    max_agents=50,
    max_users=10,
    max_storage_mb=5000,
    is_active=True
)
print(f"✅ Created tenant: {tenant}")

# Create domain for this tenant
domain = Domain.objects.create(
    domain='acme.localhost',  # Or your actual domain
    tenant=tenant,
    is_primary=True
)
print(f"✅ Created domain: {domain}")

# Verify tenant was created
print(f"\nTenant ID: {tenant.id}")
print(f"Schema Name: {tenant.schema_name}")
print(f"Name: {tenant.name}")
print(f"Slug: {tenant.slug}")

exit()
```

---

### Step 8: Create Superuser (1 minute)

```bash
python manage.py createsuperuser

# Follow prompts:
# Username: admin
# Email: admin@example.com
# Password: ********
# Password (again): ********
```

---

### Step 9: Start Server with PostgreSQL (1 minute)

```bash
cd cloud_backend
python manage.py runserver 9000
```

**Expected:**
```
✅ System check identified no issues (0 silenced).
✅ November 19, 2025 - 18:30:00
✅ Django version 5.0.14, using settings 'config.settings'
✅ Starting development server at http://127.0.0.1:9000/
✅ Quit the server with CONTROL-C.
```

---

### Step 10: Test Multi-Tenancy in Admin! (1 minute)

```bash
# Open browser
open http://localhost:9000/admin/

# Login with superuser credentials

# Navigate to:
# - Tenants > Tenants
# - Should see: "Public Schema" and "Acme Inc"
# ✅ Multi-tenancy is working!

# Try creating a new tenant:
# - Click "Add Tenant"
# - Fill in details
# - Save
# ✅ Should work without errors!
```

---

## 🎯 Verification Checklist

After completing all steps:

- [ ] PostgreSQL installed and running
- [ ] Database `agentverse_cloud` created
- [ ] `.env` file configured with PostgreSQL URL
- [ ] `psycopg2-binary` installed
- [ ] Migrations run successfully
- [ ] `tenants_tenant` table exists (verify with `\dt` in psql)
- [ ] Public tenant created
- [ ] First real tenant created
- [ ] Superuser created
- [ ] Server starts without errors
- [ ] Can access `/admin/tenants/tenant/`
- [ ] Can see both public and real tenants
- [ ] Can create new tenants via admin

---

## 🔍 Troubleshooting

### Error: "could not connect to server"

**Solution:**
```bash
# Start PostgreSQL
brew services start postgresql@14

# Check status
brew services list | grep postgresql
```

### Error: "database does not exist"

**Solution:**
```bash
createdb agentverse_cloud
```

### Error: "No module named 'psycopg2'"

**Solution:**
```bash
pip install psycopg2-binary
```

### Error: "relation tenants_tenant does not exist"

**Solution:**
```bash
# Run migrations again
python manage.py migrate

# Verify migrations were applied
python manage.py showmigrations tenants
# Should show [X] for all migrations
```

### Error: "Public tenant not found"

**Solution:**
```bash
python manage.py shell
# Run the public tenant creation code from Step 6
```

---

## 📊 What Multi-Tenancy Gives You

### With PostgreSQL + django-tenants:

✅ **Schema Isolation**
- Each tenant has its own PostgreSQL schema
- Complete data separation at database level
- No cross-tenant data leakage

✅ **Scalability**
- Add unlimited tenants
- Each tenant has isolated data
- Efficient resource usage

✅ **Security**
- Database-level isolation
- Tenant data cannot cross boundaries
- SQL injection safe across tenants

✅ **Features**
- Domain-based routing (`acme.localhost`, `customer2.localhost`)
- Tenant-specific settings
- Usage tracking per tenant
- Subscription management
- Tenant invitations

✅ **Performance**
- Efficient queries (only within tenant schema)
- No tenant_id filtering needed
- PostgreSQL optimizations

---

## 🚀 Next Steps After Setup

### 1. Test Multi-Tenant Agent Creation

```python
# In Django shell
from apps.agents.models import Agent
from django.db import connection

# Switch to tenant schema
connection.set_schema('tenant_acme')

# Create agent for this tenant
agent = Agent.objects.create(
    name='Acme Support Agent',
    description='Customer support for Acme Inc',
    llm_provider='openai',
    llm_model='gpt-4o',
    system_prompt='You are a helpful customer support agent for Acme Inc.',
    is_active=True
)
print(f"✅ Created agent: {agent}")

# Verify it's in tenant schema
agents = Agent.objects.all()
print(f"Agents in tenant_acme: {agents.count()}")
```

### 2. Test Domain Routing

**Add to `/etc/hosts`:**
```bash
sudo nano /etc/hosts

# Add:
127.0.0.1 acme.localhost
127.0.0.1 public.localhost
```

**Access tenant-specific URLs:**
- `http://acme.localhost:9000/admin/` → Acme Inc tenant
- `http://public.localhost:9000/admin/` → Public tenant
- `http://localhost:9000/admin/` → Public tenant (default)

### 3. Create More Tenants

Create tenants for different customers:
- `tenant_microsoft` → Microsoft
- `tenant_google` → Google
- `tenant_amazon` → Amazon

Each will have:
- Isolated data
- Separate PostgreSQL schema
- Own agents, users, messages

---

## 📈 Performance Comparison

### SQLite (Current - Limited)

```
❌ No multi-tenancy
❌ Single schema for all data
❌ tenant_id filtering required
❌ Cross-tenant data leakage possible
❌ Not production-ready
⚠️  Only for quick testing
```

### PostgreSQL (After Setup - Full Power)

```
✅ Full multi-tenancy
✅ Schema-based isolation
✅ No tenant_id filtering needed
✅ Zero cross-tenant leakage
✅ Production-ready
✅ Unlimited tenants
✅ Domain routing
✅ Scalable
```

---

## ⏱️ Total Setup Time

**Estimated:** 15-20 minutes

**Breakdown:**
1. Install PostgreSQL: 2 min
2. Create database: 1 min
3. Configure .env: 2 min
4. Install psycopg2: 1 min
5. Run migrations: 2 min
6. Create public tenant: 3 min
7. Create first tenant: 2 min
8. Create superuser: 1 min
9. Start server: 1 min
10. Test admin: 1 min

**Worth it?** Absolutely! Multi-tenancy is core to AgentVerse.

---

## 🎉 Success Indicators

After setup, you should see:

✅ **In Admin:**
- `/admin/tenants/tenant/` accessible
- Can create new tenants
- Can manage tenant invitations
- Can set tenant limits

✅ **In Database:**
```sql
-- Check schemas
SELECT schema_name FROM information_schema.schemata
WHERE schema_name LIKE 'tenant_%';

-- Should show:
-- public
-- tenant_acme
-- (and any other tenants you created)
```

✅ **In Django Shell:**
```python
from apps.tenants.models import Tenant
print(Tenant.objects.all())
# Should show: [<Tenant: Public Schema>, <Tenant: Acme Inc>]
```

---

## 📞 Need Help?

If you run into issues:

1. **Check PostgreSQL is running:**
   ```bash
   brew services list | grep postgresql
   ```

2. **Check database exists:**
   ```bash
   psql -l | grep agentverse
   ```

3. **Check migrations:**
   ```bash
   python manage.py showmigrations
   ```

4. **Check .env file:**
   ```bash
   cat .env | grep DATABASE_URL
   ```

5. **Test connection:**
   ```bash
   python manage.py dbshell
   # Should connect to PostgreSQL
   ```

---

## 🎯 CRITICAL PRIORITY

**Multi-tenancy IS the most crucial part of AgentVerse.**

**Without PostgreSQL:**
- ❌ No tenant isolation
- ❌ No SaaS capability
- ❌ No scalability
- ❌ Security concerns
- ❌ Not production-ready

**With PostgreSQL:**
- ✅ Full multi-tenancy
- ✅ Complete SaaS platform
- ✅ Unlimited scalability
- ✅ Enterprise-grade security
- ✅ Production-ready

---

## 🚀 Let's Get Multi-Tenancy Working!

**Follow the steps above and multi-tenancy will work perfectly.**

**Total Time:** 15-20 minutes
**Result:** Fully functional multi-tenant SaaS platform

---

**Ready to set up PostgreSQL now?**

Just follow Steps 1-10 above and you'll have full multi-tenancy working in less than 20 minutes! 🎉

**Let me know when you're ready to start or if you need help with any step!**
