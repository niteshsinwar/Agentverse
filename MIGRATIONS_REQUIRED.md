# Django Migrations Required

## Summary

The cloud backend models have been updated to add explicit `tenant` ForeignKey fields for multi-tenancy support. These changes require database migrations to be generated and applied.

## Models Modified

All the following models now have an explicit `tenant` field:

### 1. apps/agents/models.py
- **Model**: `Agent`
- **Change**: Added `tenant` ForeignKey field
- **Index**: Added `tenant` to indexes
- **Auto-set**: `save()` method auto-sets tenant from schema context

### 2. apps/tools/models.py
- **Model**: `Tool`
- **Change**: Added `tenant` ForeignKey field
- **Index**: Added `tenant` to indexes
- **Auto-set**: `save()` method auto-sets tenant from schema context

### 3. apps/mcp/models.py
- **Model**: `MCPServer`
- **Change**: Added `tenant` ForeignKey field
- **Index**: Added `tenant` to indexes
- **Auto-set**: `save()` method auto-sets tenant from schema context

### 4. apps/groups/models.py
- **Model**: `Group`
- **Change**: Added `tenant` ForeignKey field
- **Index**: Added `tenant`, `name` indexes
- **Constraint**: Added `unique_together = [['tenant', 'name']]`
- **Auto-set**: `save()` method auto-sets tenant from schema context

### 5. apps/messages/models.py
- **Model**: `Message`
- **Change**: Added `tenant` ForeignKey field
- **Index**: Added composite indexes with `tenant`
- **Auto-set**: `save()` method auto-sets tenant from schema context

### 6. apps/documents/models.py
- **Model**: `Document`
- **Change**: Added `tenant` ForeignKey field
- **Index**: Added `tenant` to indexes
- **Auto-set**: `save()` method auto-sets tenant from schema context

### 7. apps/tenants/models.py
- **Model**: `TenantMembership` (NEW)
- **Purpose**: Many-to-many relationship between users and tenants
- **Fields**: `id`, `tenant`, `user`, `role`, `is_active`, `joined_at`
- **Constraint**: `unique_together = [['tenant', 'user']]`

## Migration Commands

Run these commands in your cloud_backend environment:

```bash
# Navigate to cloud backend
cd cloud_backend

# Activate virtual environment (if applicable)
source venv/bin/activate  # or your venv path

# Generate migrations
python manage.py makemigrations agents
python manage.py makemigrations tools
python manage.py makemigrations mcp
python manage.py makemigrations groups
python manage.py makemigrations messages
python manage.py makemigrations documents
python manage.py makemigrations tenants

# Or generate all at once
python manage.py makemigrations
```

## Data Migration Required

⚠️ **CRITICAL**: Before applying migrations, you need to populate `tenant_id` for existing records.

### Steps:

1. **Create data migration for each app**:
   ```bash
   python manage.py makemigrations --empty agents --name populate_tenant_id
   python manage.py makemigrations --empty tools --name populate_tenant_id
   python manage.py makemigrations --empty mcp --name populate_tenant_id
   python manage.py makemigrations --empty groups --name populate_tenant_id
   python manage.py makemigrations --empty messages --name populate_tenant_id
   python manage.py makemigrations --empty documents --name populate_tenant_id
   ```

2. **Edit each migration** to add forward/reverse functions:
   ```python
   def populate_tenant_id(apps, schema_editor):
       """Populate tenant_id for existing records"""
       Tenant = apps.get_model('tenants', 'Tenant')
       Agent = apps.get_model('agents', 'Agent')

       # Get default tenant (or handle appropriately)
       try:
           default_tenant = Tenant.objects.first()
           if default_tenant:
               Agent.objects.filter(tenant_id__isnull=True).update(
                   tenant_id=default_tenant.id
               )
       except Tenant.DoesNotExist:
           pass

   class Migration(migrations.Migration):
       dependencies = [
           ('agents', '000X_add_tenant_field'),
           ('tenants', '0001_initial'),
       ]

       operations = [
           migrations.RunPython(populate_tenant_id, migrations.RunPython.noop),
       ]
   ```

3. **Apply migrations**:
   ```bash
   python manage.py migrate
   ```

## Verification Steps

After migrations are applied, verify:

1. **Check tables have tenant_id column**:
   ```sql
   -- PostgreSQL
   \d+ agents_agent
   \d+ tools_tool
   \d+ mcp_mcpserver
   \d+ groups_group
   \d+ messages_message
   \d+ documents_document
   ```

2. **Check indexes created**:
   ```sql
   SELECT indexname FROM pg_indexes WHERE tablename = 'agents_agent';
   ```

3. **Verify unique constraints**:
   ```sql
   SELECT conname FROM pg_constraint WHERE conrelid = 'groups_group'::regclass;
   ```

4. **Test tenant isolation**:
   ```python
   # In Django shell
   from apps.agents.models import Agent
   from apps.tenants.models import Tenant

   tenant1 = Tenant.objects.first()
   agents = Agent.objects.filter(tenant=tenant1)
   print(f"Tenant {tenant1.name} has {agents.count()} agents")
   ```

## Rollback Plan

If migrations fail:

1. **Rollback migrations**:
   ```bash
   python manage.py migrate agents <previous_migration_name>
   python manage.py migrate tools <previous_migration_name>
   # ... etc
   ```

2. **Delete migration files**:
   ```bash
   rm apps/agents/migrations/000X_add_tenant.py
   rm apps/tools/migrations/000X_add_tenant.py
   # ... etc
   ```

3. **Restore from backup** (if database was modified)

## Production Deployment

For production deployment:

1. **Backup database first**:
   ```bash
   pg_dump -U postgres agentverse > backup_before_tenant_migration.sql
   ```

2. **Test migrations on staging environment first**

3. **Schedule downtime** (if needed) for migration execution

4. **Monitor migration progress**:
   ```bash
   python manage.py migrate --verbosity 2
   ```

5. **Verify data integrity after migration**

## Related Changes

These migrations are part of the multi-tenancy security fixes:

- **Security**: TenantFilteredAdmin applied to all admin classes
- **Security**: All ViewSets now filter by tenant
- **API**: All serializers include `tenant_id` in responses
- **Local Backend**: Cache now tenant-isolated
- **Local Backend**: Cloud client passes X-Tenant-ID header

## References

- Git commit: 4814081 - Applied TenantFilteredAdmin
- Git commit: 84de12d - Secured ViewSets with tenant filtering
- Git commit: 63628f5 - Added tenant_id to serializers
- Git commit: ab67669 - Local backend cache tenant isolation
- Git commit: d3f1ff9 - Cloud client X-Tenant-ID header
