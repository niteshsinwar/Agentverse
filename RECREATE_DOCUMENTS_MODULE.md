# 🔧 CRITICAL FIX: Recreate Missing Documents Module

## Issue
The `cloud_backend/apps/documents/` module exists in the repository but is not syncing to local machines, causing the cloud backend to fail to start with:
```
ModuleNotFoundError: No module named 'apps.documents'
```

## Solution: Manual Recreation

Follow these steps **exactly** to recreate the documents module on your local machine.

---

## Step 1: Create Directory Structure

```bash
cd cloud_backend/apps
mkdir -p documents/migrations
cd documents
```

---

## Step 2: Create `__init__.py`

```bash
cat > __init__.py << 'EOF'
# Documents app - Document management and storage
EOF
```

---

## Step 3: Create `apps.py`

```bash
cat > apps.py << 'EOF'
from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.documents'
    verbose_name = 'Documents'
EOF
```

---

## Step 4: Create `models.py`

```bash
cat > models.py << 'EOF'
from django.db import models
from apps.core.models import TimeStampedModel

class Document(TimeStampedModel):
    group = models.UUIDField(help_text="Group ID this document belongs to")
    filename = models.CharField(max_length=500, help_text="Original filename")
    storage_path = models.CharField(max_length=1000, help_text="Path in storage (MinIO/S3)")
    file_size = models.BigIntegerField(help_text="File size in bytes")
    file_type = models.CharField(max_length=100, help_text="MIME type")
    uploaded_by = models.UUIDField(help_text="User ID who uploaded")
    embeddings_indexed = models.BooleanField(default=False, help_text="Whether embeddings are in Qdrant")
    qdrant_collection = models.CharField(max_length=255, blank=True, null=True)
    metadata = models.JSONField(default=dict, help_text="Additional metadata")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['group', 'created_at']),
            models.Index(fields=['uploaded_by']),
        ]

    def __str__(self):
        return self.filename
EOF
```

---

## Step 5: Create `serializers.py`

```bash
cat > serializers.py << 'EOF'
from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    file_size_mb = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'uploaded_by', 'storage_path']

    def get_file_size_mb(self, obj):
        return round(obj.file_size / (1024 * 1024), 2)
EOF
```

---

## Step 6: Create `views.py`

```bash
cat > views.py << 'EOF'
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Document
from .serializers import DocumentSerializer

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['group', 'uploaded_by', 'file_type']

    @action(detail=False, methods=['post'])
    def upload(self, request):
        # TODO: Implement MinIO/S3 upload
        return Response({'message': 'Upload endpoint - implement MinIO integration'}, status=status.HTTP_501_NOT_IMPLEMENTED)
EOF
```

---

## Step 7: Create `urls.py`

```bash
cat > urls.py << 'EOF'
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.DocumentViewSet, basename='document')

urlpatterns = [path('', include(router.urls))]
EOF
```

---

## Step 8: Create `admin.py`

```bash
cat > admin.py << 'EOF'
"""
Django Admin for Documents
"""

from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for Document model"""

    list_display = (
        'filename',
        'file_type',
        'file_size_display',
        'group',
        'embeddings_indexed',
        'created_at',
    )

    list_filter = (
        'file_type',
        'embeddings_indexed',
        'created_at',
    )

    search_fields = (
        'filename',
        'storage_path',
        'group',
    )

    readonly_fields = (
        'id',
        'file_size_display',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Document Info', {
            'fields': ('filename', 'file_type', 'file_size_display', 'group')
        }),
        ('Storage', {
            'fields': ('storage_path',)
        }),
        ('Vector Embeddings', {
            'fields': ('embeddings_indexed', 'qdrant_collection')
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'metadata', 'id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 50

    def file_size_display(self, obj):
        """Display file size in human-readable format"""
        size_bytes = obj.file_size

        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    file_size_display.short_description = 'File Size'
EOF
```

---

## Step 9: Create Migrations Directory

```bash
cd migrations
cat > __init__.py << 'EOF'
EOF
```

---

## Step 10: Verify Structure

```bash
cd ../../..  # Back to cloud_backend/
tree apps/documents/
```

Expected output:
```
apps/documents/
├── __init__.py
├── admin.py
├── apps.py
├── migrations/
│   └── __init__.py
├── models.py
├── serializers.py
├── urls.py
└── views.py
```

---

## Step 11: Run Migrations

```bash
cd cloud_backend
python manage.py makemigrations documents
python manage.py migrate
```

---

## Step 12: Test Cloud Backend

```bash
python manage.py runserver 9000
```

You should see:
```
✅ System check identified no issues (0 silenced).
✅ Django version 5.0.x
✅ Starting development server at http://127.0.0.1:9000/
```

---

## Step 13: Verify in Browser

Visit: http://localhost:9000/admin/

You should see **Documents** in the admin panel.

---

## Alternative: Quick Script

Save this as `recreate_documents.sh`:

```bash
#!/bin/bash

cd cloud_backend/apps
mkdir -p documents/migrations
cd documents

# Create all files
cat > __init__.py << 'EOFA'
# Documents app - Document management and storage
EOFA

cat > apps.py << 'EOFB'
from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.documents'
    verbose_name = 'Documents'
EOFB

cat > models.py << 'EOFC'
from django.db import models
from apps.core.models import TimeStampedModel

class Document(TimeStampedModel):
    group = models.UUIDField(help_text="Group ID this document belongs to")
    filename = models.CharField(max_length=500, help_text="Original filename")
    storage_path = models.CharField(max_length=1000, help_text="Path in storage (MinIO/S3)")
    file_size = models.BigIntegerField(help_text="File size in bytes")
    file_type = models.CharField(max_length=100, help_text="MIME type")
    uploaded_by = models.UUIDField(help_text="User ID who uploaded")
    embeddings_indexed = models.BooleanField(default=False, help_text="Whether embeddings are in Qdrant")
    qdrant_collection = models.CharField(max_length=255, blank=True, null=True)
    metadata = models.JSONField(default=dict, help_text="Additional metadata")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['group', 'created_at']),
            models.Index(fields=['uploaded_by']),
        ]

    def __str__(self):
        return self.filename
EOFC

cat > serializers.py << 'EOFD'
from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    file_size_mb = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'uploaded_by', 'storage_path']

    def get_file_size_mb(self, obj):
        return round(obj.file_size / (1024 * 1024), 2)
EOFD

cat > views.py << 'EOFE'
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Document
from .serializers import DocumentSerializer

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['group', 'uploaded_by', 'file_type']

    @action(detail=False, methods=['post'])
    def upload(self, request):
        # TODO: Implement MinIO/S3 upload
        return Response({'message': 'Upload endpoint - implement MinIO integration'}, status=status.HTTP_501_NOT_IMPLEMENTED)
EOFE

cat > urls.py << 'EOFF'
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.DocumentViewSet, basename='document')

urlpatterns = [path('', include(router.urls))]
EOFF

cat > admin.py << 'EOFG'
from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        'filename',
        'file_type',
        'file_size_display',
        'group',
        'embeddings_indexed',
        'created_at',
    )

    list_filter = (
        'file_type',
        'embeddings_indexed',
        'created_at',
    )

    search_fields = (
        'filename',
        'storage_path',
        'group',
    )

    readonly_fields = (
        'id',
        'file_size_display',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Document Info', {
            'fields': ('filename', 'file_type', 'file_size_display', 'group')
        }),
        ('Storage', {
            'fields': ('storage_path',)
        }),
        ('Vector Embeddings', {
            'fields': ('embeddings_indexed', 'qdrant_collection')
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'metadata', 'id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 50

    def file_size_display(self, obj):
        size_bytes = obj.file_size
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    file_size_display.short_description = 'File Size'
EOFG

cd migrations
touch __init__.py

echo "✅ Documents module created successfully!"
echo "Run: cd cloud_backend && python manage.py makemigrations documents && python manage.py migrate"
```

Then run:
```bash
chmod +x recreate_documents.sh
./recreate_documents.sh
```

---

## Troubleshooting

### Issue: Module still not found
**Solution:** Make sure `INSTALLED_APPS` in `settings.py` has:
```python
TENANT_APPS = [
    ...
    'apps.documents',  # or 'apps.documents.apps.DocumentsConfig'
    ...
]
```

### Issue: Migration errors
**Solution:** Delete migrations and recreate:
```bash
rm -rf cloud_backend/apps/documents/migrations/
mkdir cloud_backend/apps/documents/migrations/
touch cloud_backend/apps/documents/migrations/__init__.py
python manage.py makemigrations documents
python manage.py migrate
```

### Issue: Import errors
**Solution:** Make sure all `__init__.py` files exist:
```bash
touch cloud_backend/apps/documents/__init__.py
touch cloud_backend/apps/documents/migrations/__init__.py
```

---

## Why This Happened

The documents module exists in the repository but may not be tracked by git properly, or there's a `.gitignore` issue. After recreating locally, you should commit it:

```bash
git add cloud_backend/apps/documents/
git commit -m "Add documents module (was missing locally)"
git push
```

---

## Verification Checklist

- [ ] Directory `cloud_backend/apps/documents/` exists
- [ ] All 8 files created (`__init__.py`, `apps.py`, `models.py`, etc.)
- [ ] Migrations directory created with `__init__.py`
- [ ] `python manage.py check` runs without errors
- [ ] `python manage.py runserver 9000` starts successfully
- [ ] Admin panel shows Documents section
- [ ] No import errors

---

**Status:** Ready to fix the critical blocker
**Time to fix:** 2-3 minutes
**Risk:** Low (simple file recreation)

Copy the files exactly as shown, run migrations, and the cloud backend will start successfully! 🚀
