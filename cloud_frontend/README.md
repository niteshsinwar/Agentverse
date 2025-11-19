# AgentVerse Cloud Frontend

**Admin Interface for Multi-Tenant Platform Management**

## Overview

The cloud frontend is the **Django Admin interface** for managing the AgentVerse multi-tenant SaaS platform. It provides a comprehensive admin panel for the AgentVerse team to manage:

- **Tenants**: Organizations using the platform
- **Users**: User accounts across all tenants
- **Agents**: AI agent configurations
- **Tools**: Custom tool implementations
- **MCP Servers**: Model Context Protocol servers
- **Groups**: Conversation groups
- **Messages**: Chat messages and history
- **Documents**: Uploaded files and embeddings
- **Analytics**: Usage logs and metrics

## Access

⚠️ **Private Network Only**

This admin interface is **NOT** accessible to end users. It is:
- Only accessible within AgentVerse's private network
- Requires superuser credentials
- Used exclusively by the AgentVerse team
- For platform management and support

## URL

```
http://localhost:9000/admin/
https://agentverse-cloud.onrender.com/admin/  (Production)
```

## Features

### 1. Tenant Management
- Create/edit/delete tenants
- Manage tenant domains (e.g., acme.agentverse.com)
- Configure license tiers (Free, Pro, Enterprise)
- Monitor usage and quotas
- Manage subscriptions and billing

### 2. User Management
- View all users across tenants
- Create admin users
- Reset passwords
- Manage permissions
- Track login history

### 3. Agent Configuration
- Browse all agents across tenants
- Edit agent system prompts
- Configure LLM providers and models
- View agent usage statistics

### 4. Tools & MCP Management
- View all custom tools
- Edit tool code
- Manage MCP server configurations
- Test tool executions

### 5. Content Management
- Browse messages across groups
- View uploaded documents
- Monitor storage usage
- Manage document embeddings

### 6. Analytics Dashboard
- Usage logs
- Tenant statistics
- Message volume
- Storage metrics
- API usage

## Login

### Development
```bash
# Create superuser
cd cloud_backend
python manage.py createsuperuser

# Access admin
http://localhost:9000/admin/
```

### Production
```bash
# Create superuser via Render shell
python manage.py createsuperuser --email admin@agentverse.com

# Login at
https://your-domain.com/admin/
```

## Admin Interface Customization

The admin interface includes:

- **Custom branding**: AgentVerse logo and colors
- **Enhanced models**: Rich admin interfaces for all models
- **Inline editing**: Edit related objects without leaving the page
- **Bulk actions**: Perform actions on multiple items
- **Search & filters**: Quick find with advanced filtering
- **Audit trail**: Track changes and usage
- **Data visualization**: Charts and graphs for analytics

## Security

### Authentication
- Django admin login required
- Superuser access only
- Session management
- CSRF protection

### Network Security
- Private network access only
- IP whitelisting (production)
- HTTPS required in production
- Rate limiting enabled

### Data Security
- Schema-based tenant isolation
- Read-only access for support staff
- Audit logging for all changes
- Regular security audits

## Admin Modules

### Apps Available in Admin

| App | Models | Description |
|-----|--------|-------------|
| **Tenants** | Tenant, Domain, TenantSettings, TenantInvitation | Multi-tenant management |
| **Users** | User | User accounts (tenant-aware) |
| **Agents** | Agent | AI agent configurations |
| **Tools** | Tool | Custom tool implementations |
| **MCP** | MCPServer | MCP server configurations |
| **Groups** | Group | Conversation groups |
| **Messages** | Message | Chat messages |
| **Documents** | Document | File uploads and embeddings |
| **Analytics** | UsageLog | Usage tracking and metrics |

## Common Admin Tasks

### Creating a New Tenant

1. Go to **Tenants** → **Add Tenant**
2. Fill in:
   - Name (e.g., "ACME Corporation")
   - Slug (e.g., "acme")
   - Email
   - License Type
3. Add domain:
   - Domain: `acme.agentverse.com`
   - Mark as primary
4. Save

The tenant schema will be created automatically.

### Managing User Roles

1. Go to **Users** → Select user
2. Edit **Role** field:
   - `admin`: Can create/edit agents and tools
   - `user`: Can only use agents
3. Set **is_staff** for Django admin access
4. Save

### Monitoring Usage

1. Go to **Analytics** → **Usage Logs**
2. Filter by:
   - Tenant
   - Action type
   - Date range
3. Export data for analysis

### Resetting Monthly Quotas

1. Go to **Tenants** → Select tenants
2. Choose action: **Reset monthly usage**
3. Confirm

## Deployment

### Development Setup

```bash
cd cloud_backend

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver 0.0.0.0:9000

# Access admin
http://localhost:9000/admin/
```

### Production Setup

```bash
# Already configured in render.yaml
# Superuser created via build.sh or manually via shell

# Access
https://your-domain.com/admin/
```

## Customization

The admin interface can be further customized:

### Custom Templates
Place in `cloud_backend/templates/admin/`:
- `base_site.html`: Custom branding
- `index.html`: Dashboard customization
- Model-specific templates

### Custom Actions
Add to `admin.py`:
```python
@admin.action(description='Custom action')
def custom_action(modeladmin, request, queryset):
    # Your custom logic
    pass
```

### Custom Filters
```python
class CustomFilter(admin.SimpleListFilter):
    title = 'Custom Filter'
    parameter_name = 'custom'

    def lookups(self, request, model_admin):
        return [('option1', 'Option 1')]

    def queryset(self, request, queryset):
        return queryset.filter(...)
```

## Troubleshooting

### Cannot Access Admin

**Problem**: 404 or permission denied

**Solutions**:
- Verify user has `is_staff = True`
- Check user has `is_superuser = True` for full access
- Verify URL: `/admin/` (with trailing slash)
- Check ALLOWED_HOSTS in settings

### Tenant Data Not Showing

**Problem**: Empty data in admin

**Solutions**:
- Verify you're in correct schema
- Check tenant is active
- Run migrations: `python manage.py migrate_schemas`
- Verify domain routing

### Performance Issues

**Problem**: Admin pages load slowly

**Solutions**:
- Enable database connection pooling
- Add indexes to frequently queried fields
- Use `select_related()` and `prefetch_related()`
- Enable caching in settings

## Support

For admin-related issues:
1. Check logs: `cloud_backend/logs/`
2. Enable Django debug toolbar
3. Contact platform team

## Next Steps

1. Set up custom admin dashboard with analytics
2. Add data export functionality
3. Implement bulk import for tenants/users
4. Create admin API for automation
5. Add email notifications for critical events

## Resources

- [Django Admin Documentation](https://docs.djangoproject.com/en/stable/ref/contrib/admin/)
- [django-tenants](https://django-tenants.readthedocs.io/)
- AgentVerse Cloud Backend docs
