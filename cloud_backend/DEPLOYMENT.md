# 🚀 Render.com Deployment Guide

## Quick Deploy (5 Minutes)

### Option 1: One-Click Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/your-org/agentverse)

### Option 2: Manual Deploy

1. **Push to GitHub**
   ```bash
   git add cloud_backend/
   git commit -m "Add production deployment config"
   git push origin main
   ```

2. **Create Render Account**
   - Go to https://render.com
   - Sign up with GitHub
   - Connect your repository

3. **Deploy Using Blueprint**
   - Click "New" → "Blueprint"
   - Select repository: `your-org/agentverse`
   - Render will detect `render.yaml`
   - Click "Apply"

4. **Wait for Deployment** (~5-10 minutes)
   - PostgreSQL database will be created
   - Redis instance will be created
   - Web service, Worker, and Beat will be deployed

---

## Post-Deployment Setup

### 1. Create Superuser

```bash
# In Render Dashboard → agentverse-cloud → Shell
python manage.py createsuperuser
# Email: admin@agentverse.com
# Name: Admin
# Password: <secure-password>
```

### 2. Create First Tenant

```bash
python manage.py shell << EOF
from apps.tenants.models import Tenant, Domain

# Create demo tenant
tenant = Tenant.objects.create(
    schema_name='demo',
    name='Demo Company',
    license_tier='pro',
    is_active=True
)

# Add custom domain
Domain.objects.create(
    domain='demo.agentverse.com',  # Update with your domain
    tenant=tenant,
    is_primary=True
)

print(f"✅ Tenant created: {tenant.name}")
EOF

# Run migrations for new tenant
python manage.py migrate_schemas --schema=demo
```

### 3. Configure Environment Variables

In Render Dashboard → agentverse-cloud → Environment:

```bash
# Required (set manually)
SENDGRID_API_KEY=SG.xxxxx
MINIO_ENDPOINT=your-minio-endpoint.com:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
QDRANT_HOST=your-qdrant-host.com
QDRANT_API_KEY=your-qdrant-api-key
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Optional (already set by render.yaml)
ALLOWED_HOSTS=agentverse-cloud.onrender.com,*.agentverse.com
CORS_ALLOWED_ORIGINS=https://app.agentverse.com
DEBUG=False
```

### 4. Set Up Custom Domain

#### In Render:
1. Go to agentverse-cloud → Settings → Custom Domains
2. Add domain: `api.agentverse.com`
3. Follow DNS instructions (add CNAME)

#### In DNS Provider (Cloudflare/Route53):
```
# API subdomain
api.agentverse.com     CNAME    agentverse-cloud.onrender.com

# Wildcard for tenants
*.agentverse.com       CNAME    agentverse-cloud.onrender.com
```

#### Update Environment:
```bash
ALLOWED_HOSTS=api.agentverse.com,*.agentverse.com
CORS_ALLOWED_ORIGINS=https://app.agentverse.com,https://agentverse.com
```

### 5. Enable HTTPS

Render automatically provides SSL certificates via Let's Encrypt.

---

## Service Architecture on Render

```
┌─────────────────────────────────────────────────────┐
│                  Render Platform                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────────┐    ┌───────────────────┐     │
│  │  Web Service    │────│  PostgreSQL DB    │     │
│  │  (Django/Gun.)  │    │  Multi-Tenant     │     │
│  │  Port: 10000    │    │                   │     │
│  └────────┬────────┘    └───────────────────┘     │
│           │                                         │
│           │              ┌───────────────────┐     │
│           ├──────────────│  Redis Cache      │     │
│           │              │  & Channels       │     │
│           │              └───────────────────┘     │
│           │                                         │
│  ┌────────┴────────┐                               │
│  │  Celery Worker  │    External Services:         │
│  │  (Background)   │    - SendGrid (Email)         │
│  └─────────────────┘    - MinIO/S3 (Files)         │
│                          - Qdrant (Vectors)         │
│  ┌─────────────────┐    - Stripe (Payments)        │
│  │  Celery Beat    │                               │
│  │  (Scheduler)    │                               │
│  └─────────────────┘                               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Monitoring & Logs

### View Logs
```bash
# In Render Dashboard → Service → Logs
# Or use Render CLI:
render logs -s agentverse-cloud -n 100
```

### Health Checks
- Endpoint: `https://api.agentverse.com/health/`
- Expected: `{"status":"healthy","service":"agentverse-cloud","version":"1.0.0"}`

### Metrics
- Render Dashboard shows:
  - CPU usage
  - Memory usage
  - Request rate
  - Response time

---

## Scaling

### Vertical Scaling (Upgrade Plan)
```
Starter   → $7/mo   - 512MB RAM, Shared CPU
Standard  → $25/mo  - 2GB RAM, 1 CPU
Pro       → $85/mo  - 4GB RAM, 2 CPU
```

### Horizontal Scaling
```yaml
# In render.yaml:
services:
  - type: web
    name: agentverse-cloud
    plan: standard
    scaling:
      minInstances: 2    # Always 2 instances
      maxInstances: 10   # Scale up to 10
      targetMemoryPercent: 75
      targetCPUPercent: 75
```

---

## Database Backups

Render automatically backs up PostgreSQL:
- Daily backups (retained for 7 days)
- Manual backups available in dashboard

### Manual Backup
```bash
# Download backup
render db backup agentverse-db

# Restore from backup
render db restore agentverse-db <backup-id>
```

---

## CI/CD Pipeline

### Auto-Deploy on Push
Render automatically deploys when you push to `main`:

```bash
git add .
git commit -m "Update feature"
git push origin main
# Render auto-detects changes and deploys
```

### Manual Deploy
```bash
# In Render Dashboard:
# Service → Manual Deploy → Deploy latest commit
```

### Preview Deployments
```yaml
# Add to render.yaml for PR previews:
services:
  - type: web
    name: agentverse-cloud
    previewsEnabled: yes  # Creates preview env for each PR
```

---

## Cost Estimate (Monthly)

```
PostgreSQL (Starter)    $7
Redis (Starter)         $10
Web Service (Standard)  $25
Celery Worker (Starter) $7
Celery Beat (Starter)   $7
────────────────────────────
Total                   $56/month

+ External services:
  - SendGrid: $15-$50
  - MinIO/S3: $5-$50
  - Qdrant: Free (self-hosted) or $25-$100
  - Stripe: Pay-as-you-go
```

---

## Troubleshooting

### Issue: Build Fails

**Check:**
1. Python version in `render.yaml` matches `requirements.txt`
2. All required env vars are set
3. Database migrations are successful

**Solution:**
```bash
# In Render Shell:
python --version
pip list
python manage.py check
```

### Issue: Service Crashes

**Check logs:**
```bash
render logs -s agentverse-cloud --tail
```

**Common causes:**
- Missing environment variables
- Database connection errors
- Out of memory (upgrade plan)

### Issue: Slow Performance

**Solutions:**
1. Upgrade to Standard plan (more RAM/CPU)
2. Enable Redis caching
3. Add database indexes
4. Use CDN for static files

---

## Security Checklist

- [ ] `DEBUG=False` in production
- [ ] Strong `DJANGO_SECRET_KEY` (auto-generated by Render)
- [ ] HTTPS enforced (automatic on Render)
- [ ] `ALLOWED_HOSTS` configured correctly
- [ ] `CORS_ALLOWED_ORIGINS` restricted
- [ ] Database credentials secure (managed by Render)
- [ ] API rate limiting enabled
- [ ] Sentry error tracking configured (optional)

---

## Next Steps

1. ✅ Deploy to Render
2. ✅ Set up custom domain
3. ✅ Create first tenant
4. 📧 Configure SendGrid for emails
5. 📦 Set up MinIO/S3 for file storage
6. 🔍 Configure Qdrant for vector search
7. 💳 Integrate Stripe for payments
8. 📊 Set up monitoring (Sentry/DataDog)
9. 🚀 Deploy local frontend/backend to user devices
10. 🎉 Launch!

---

## Support Resources

- Render Docs: https://render.com/docs
- Django-Tenants: https://django-tenants.readthedocs.io
- Community: https://community.render.com
