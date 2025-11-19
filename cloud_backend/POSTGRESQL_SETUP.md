# 🐘 PostgreSQL Production Setup Guide

## Prerequisites

- PostgreSQL 14+ installed
- Superuser access to PostgreSQL
- Python 3.11+ with virtual environment

---

## Quick Setup (Local PostgreSQL)

### 1. Install PostgreSQL

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql@14
brew services start postgresql@14

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL console:
CREATE DATABASE agentverse_cloud;
CREATE USER agentverse_admin WITH PASSWORD 'your_secure_password';
ALTER ROLE agentverse_admin SET client_encoding TO 'utf8';
ALTER ROLE agentverse_admin SET default_transaction_isolation TO 'read committed';
ALTER ROLE agentverse_admin SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE agentverse_cloud TO agentverse_admin;

# Grant schema creation permissions (required for django-tenants)
\c agentverse_cloud
GRANT ALL ON SCHEMA public TO agentverse_admin;
ALTER DATABASE agentverse_cloud OWNER TO agentverse_admin;

\q
```

### 3. Update Environment Variables

```bash
cd cloud_backend

# Create/update .env file
cat > .env << EOF
# Database
DATABASE_URL=postgresql://agentverse_admin:your_secure_password@localhost:5432/agentverse_cloud

# Security
DJANGO_SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=False

# Redis (for production)
REDIS_URL=redis://localhost:6379/0

# Email (SendGrid)
SENDGRID_API_KEY=your_sendgrid_api_key
DEFAULT_FROM_EMAIL=noreply@agentverse.com

# Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=agentverse-documents

# Vector DB
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=

# Stripe (optional)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
EOF
```

### 4. Run Multi-Tenant Migrations

```bash
# Activate virtual environment
source venv/bin/activate

# Set environment
export DATABASE_URL="postgresql://agentverse_admin:your_secure_password@localhost:5432/agentverse_cloud"
export DJANGO_SECRET_KEY="your-secret-key"
export DEBUG="False"

# Install dependencies (if not already)
pip install -r requirements.txt

# Create shared schema migrations
python manage.py makemigrations

# Run migrations for shared schema (public)
python manage.py migrate_schemas --shared

# Create public tenant (required for django-tenants)
python manage.py shell << EOF
from apps.tenants.models import Tenant, Domain

# Create public tenant
public_tenant = Tenant.objects.create(
    schema_name='public',
    name='Public',
    license_tier='enterprise'
)
Domain.objects.create(
    domain='localhost',
    tenant=public_tenant,
    is_primary=True
)
print("✅ Public tenant created")
EOF

# Create superuser
python manage.py createsuperuser
```

### 5. Create Your First Tenant

```bash
python manage.py shell << EOF
from apps.tenants.models import Tenant, Domain

# Create tenant for ACME Corp
tenant = Tenant.objects.create(
    schema_name='acme',
    name='ACME Corporation',
    license_tier='pro',
    is_active=True
)

# Add domain
Domain.objects.create(
    domain='acme.localhost',  # For local testing
    tenant=tenant,
    is_primary=True
)

print(f"✅ Tenant created: {tenant.name} (schema: {tenant.schema_name})")
print(f"   Access at: http://acme.localhost:9000")
EOF
```

### 6. Run Tenant-Specific Migrations

```bash
# Migrate all tenants
python manage.py migrate_schemas

# Or migrate specific tenant
python manage.py migrate_schemas --schema=acme
```

---

## Production Setup (Render.com / Cloud)

### 1. Render.com PostgreSQL

1. Go to Render Dashboard → New → PostgreSQL
2. Choose:
   - Name: `agentverse-db`
   - Region: `Oregon (US West)`
   - PostgreSQL Version: `14`
   - Plan: `Starter` ($7/mo) or higher

3. Copy the **Internal Database URL** (looks like):
   ```
   postgresql://user:pass@dpg-xxxxx-a.oregon-postgres.render.com/agentverse_xxxxx
   ```

### 2. Update Render Environment Variables

In your Render Web Service:
```
DATABASE_URL=<internal-database-url>
DJANGO_SECRET_KEY=<generate-random-key>
DEBUG=False
ALLOWED_HOSTS=agentverse-cloud.onrender.com,*.agentverse.com
CORS_ALLOWED_ORIGINS=https://app.agentverse.com
REDIS_URL=<redis-url-from-render>
```

### 3. Run Migrations on Render

```bash
# SSH into Render instance or use Render Console
python manage.py migrate_schemas --shared
python manage.py createsuperuser
```

---

## Multi-Tenancy URL Routing

### Local Development

```bash
# Edit /etc/hosts (Linux/Mac) or C:\Windows\System32\drivers\etc\hosts (Windows)
127.0.0.1 acme.localhost
127.0.0.1 demo.localhost
127.0.0.1 test.localhost

# Access tenants:
# http://acme.localhost:9000  -> routes to 'acme' schema
# http://demo.localhost:9000  -> routes to 'demo' schema
```

### Production (Wildcard DNS)

```
# DNS Configuration (e.g., Cloudflare)
*.agentverse.com -> CNAME -> agentverse-cloud.onrender.com

# Tenants access via:
# https://acme.agentverse.com
# https://demo.agentverse.com
```

---

## Verification Checklist

- [ ] PostgreSQL running and accessible
- [ ] Database created with correct permissions
- [ ] Shared schema migrations completed
- [ ] Public tenant created
- [ ] Test tenant created (e.g., 'acme')
- [ ] Tenant-specific migrations completed
- [ ] Superuser created and can login
- [ ] Can access tenant via subdomain
- [ ] Redis connected (for cache/channels)
- [ ] MinIO/S3 accessible

---

## Common Issues

### Issue 1: Permission Denied on Schema

```sql
-- Solution: Grant all permissions
GRANT ALL ON SCHEMA public TO agentverse_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO agentverse_admin;
```

### Issue 2: Tenant Not Found

```
Error: No tenant found for domain 'acme.localhost'
```

**Solution**: Check domain exists:
```python
from apps.tenants.models import Domain
print(Domain.objects.all())
```

### Issue 3: Migration Fails

```bash
# Reset database (CAUTION: destroys all data)
sudo -u postgres psql
DROP DATABASE agentverse_cloud;
CREATE DATABASE agentverse_cloud;
GRANT ALL PRIVILEGES ON DATABASE agentverse_cloud TO agentverse_admin;
\q

# Re-run migrations
python manage.py migrate_schemas --shared
```

---

## Performance Tuning

### PostgreSQL Configuration

```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/14/main/postgresql.conf

# Recommended settings for multi-tenant:
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
work_mem = 4MB
```

### Connection Pooling (PgBouncer)

```bash
# Install PgBouncer
sudo apt install pgbouncer

# Configure /etc/pgbouncer/pgbouncer.ini
[databases]
agentverse_cloud = host=localhost port=5432 dbname=agentverse_cloud

[pgbouncer]
listen_port = 6432
listen_addr = localhost
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
```

Update Django to use PgBouncer:
```python
DATABASE_URL=postgresql://user:pass@localhost:6432/agentverse_cloud
```

---

## Backup Strategy

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/agentverse"
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U agentverse_admin agentverse_cloud | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Keep last 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete

echo "✅ Backup completed: $BACKUP_DIR/db_$DATE.sql.gz"
```

---

## Monitoring

```bash
# Check active connections per tenant
SELECT schemaname, count(*)
FROM pg_stat_activity
WHERE schemaname != 'public'
GROUP BY schemaname;

# Check database size per schema
SELECT schema_name,
       pg_size_pretty(sum(table_size)::bigint) as size
FROM (
  SELECT pg_catalog.pg_namespace.nspname as schema_name,
         pg_relation_size(pg_catalog.pg_class.oid) as table_size
  FROM pg_catalog.pg_class
  JOIN pg_catalog.pg_namespace ON relnamespace = pg_catalog.pg_namespace.oid
) t
GROUP BY schema_name
ORDER BY sum(table_size) DESC;
```

---

## Next Steps

After PostgreSQL setup:
1. Test multi-tenant isolation
2. Set up Redis for caching
3. Configure MinIO/S3 for file storage
4. Deploy to production (Render.com)
5. Set up monitoring and alerts
