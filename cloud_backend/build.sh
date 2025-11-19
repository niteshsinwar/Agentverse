#!/bin/bash
# Render.com Build Script

set -e  # Exit on error

echo "🚀 Starting AgentVerse Cloud Backend build..."

# Install Python dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "🔄 Running database migrations..."
if [ "$DATABASE_URL" != *"sqlite"* ]; then
    # PostgreSQL - run multi-tenant migrations
    python manage.py migrate_schemas --shared
    echo "✅ Shared schema migrations completed"

    # Check if public tenant exists, create if not
    python manage.py shell << EOF
from apps.tenants.models import Tenant, Domain
import sys

try:
    public_tenant = Tenant.objects.get(schema_name='public')
    print("✅ Public tenant exists")
except Tenant.DoesNotExist:
    print("📝 Creating public tenant...")
    public_tenant = Tenant.objects.create(
        schema_name='public',
        name='Public',
        license_tier='enterprise'
    )
    # Get domain from ALLOWED_HOSTS
    import os
    allowed_hosts = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')
    primary_domain = allowed_hosts[0] if allowed_hosts else 'localhost'
    Domain.objects.create(
        domain=primary_domain,
        tenant=public_tenant,
        is_primary=True
    )
    print(f"✅ Public tenant created with domain: {primary_domain}")
EOF

    # Migrate all existing tenants
    echo "🔄 Migrating all tenants..."
    python manage.py migrate_schemas
    echo "✅ All tenant migrations completed"
else
    # SQLite - regular migrations
    python manage.py migrate
    echo "✅ SQLite migrations completed"
fi

echo "✅ Build completed successfully!"
