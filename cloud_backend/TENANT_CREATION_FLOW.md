# Tenant Creation Flow - Architecture Guide

**Date:** 2025-11-20
**Architecture:** Superadmin → Tenant → Users (No Signup)

---

## Overview

**Key Principle:** Tenants are NOT self-service. Only superadmin can create tenants.

### User Roles

1. **Superadmin** (Platform Admin)
   - Creates tenants
   - Creates initial tenant admin user
   - Manages subscriptions
   - Views analytics

2. **Tenant Admin**
   - Creates users in their tenant
   - Manages tenant resources (agents, groups, etc.)
   - Updates tenant settings

3. **Tenant User**
   - Uses agents and groups
   - Cannot create other users

---

## Creation Flow

```
┌─────────────┐
│ Superadmin  │
└──────┬──────┘
       │ 1. Creates Tenant + Tenant Admin
       ▼
┌─────────────────────────────┐
│ Cloud Backend               │
│ POST /api/v1/tenants/admin/ │
│       tenants/              │
└──────┬──────────────────────┘
       │ 2. Creates:
       │    - Tenant record
       │    - Database schema
       │    - Primary domain
       │    - Admin user
       │    - TenantMembership
       ▼
┌─────────────┐
│Tenant Admin │
└──────┬──────┘
       │ 3. Logs in to local frontend
       │    (email + password + tenant_id)
       ▼
┌──────────────────┐
│ Creates Users    │
│ in Tenant        │
└──────────────────┘
```

---

## 1. Superadmin Creates Tenant

### Endpoint

```
POST /api/v1/tenants/admin/tenants/
Authorization: Bearer {superadmin_jwt}
Content-Type: application/json
```

### Request Body

```json
{
  "name": "Acme Corporation",
  "slug": "acme",
  "email": "admin@acme.com",
  "admin_name": "John Doe",
  "admin_email": "john@acme.com",
  "admin_password": "SecureP@ssw0rd!",
  "license_type": "pro",
  "company_size": "51-200",
  "industry": "Technology",
  "phone": "+1234567890"
}
```

### Required Fields

- `name`: Company name
- `email`: Primary contact email (can be same as admin_email)
- `admin_email`: Tenant admin login email
- `admin_password`: Tenant admin password

### Optional Fields

- `slug`: URL slug (auto-generated from name if omitted)
- `admin_name`: Admin user's full name
- `license_type`: free/pro/enterprise (default: free)
- `company_size`: 1-10, 11-50, 51-200, 201-1000, 1001+
- `industry`: e.g., "Technology", "Healthcare", etc.
- `phone`: Contact phone number

### Response

```json
{
  "tenant": {
    "id": "uuid",
    "name": "Acme Corporation",
    "slug": "acme",
    "schema_name": "tenant_acme",
    "email": "admin@acme.com",
    "admin_name": "John Doe",
    "license_type": "pro",
    "is_active": true,
    "created_at": "2025-11-20T10:00:00Z"
  },
  "admin_user": {
    "id": "uuid",
    "email": "john@acme.com",
    "name": "John Doe",
    "role": "admin"
  },
  "domain": "acme.agentverse.com",
  "message": "Tenant and admin user created successfully"
}
```

### What Happens Behind the Scenes

1. **Tenant Creation**
   - Creates `Tenant` record in public schema
   - Auto-generates `schema_name` from slug: `tenant_{slug}`
   - Sets license limits based on `license_type`

2. **Schema Creation**
   - Django-tenants automatically creates PostgreSQL schema
   - All tenant-specific tables are created in new schema

3. **Domain Creation**
   - Creates `Domain` record: `{slug}.agentverse.com`
   - Marks as primary domain

4. **Admin User Creation**
   - Switches to tenant schema
   - Creates `User` record with `role='admin'`
   - Hashes password securely

5. **TenantMembership Creation**
   - Links admin user to tenant
   - Stores relationship in public schema (users are in SHARED_APPS)

---

## 2. Tenant Admin Logs In

### Endpoint

```
POST /api/v1/auth/login/
Content-Type: application/json
```

### Request Body

```json
{
  "tenant_id": "acme",
  "email": "john@acme.com",
  "password": "SecureP@ssw0rd!"
}
```

### Response

```json
{
  "access": "jwt_token",
  "refresh": "refresh_token",
  "user": {
    "id": "uuid",
    "email": "john@acme.com",
    "name": "John Doe",
    "role": "admin"
  },
  "tenant": {
    "id": "uuid",
    "name": "Acme Corporation",
    "slug": "acme"
  }
}
```

---

## 3. Tenant Admin Creates Users

Once logged in, tenant admin can create users via:

### Django Admin (Recommended)

1. Access Django admin: `https://acme.agentverse.com/admin/`
2. Navigate to "Users"
3. Click "Add User"
4. Fill in:
   - Email
   - Name
   - Password
   - Role (admin or user)

### API (Programmatic)

```
POST /api/v1/users/
Authorization: Bearer {tenant_admin_jwt}
Content-Type: application/json
```

```json
{
  "email": "jane@acme.com",
  "name": "Jane Smith",
  "password": "AnotherSecureP@ss!",
  "role": "user"
}
```

**Note:** Only tenant admins can create users. Regular users get 403 Forbidden.

---

## 4. Users Log In

### Endpoint

```
POST /api/v1/auth/login/
Content-Type: application/json
```

### Request Body

```json
{
  "tenant_id": "acme",
  "email": "jane@acme.com",
  "password": "AnotherSecureP@ss!"
}
```

### Response

```json
{
  "access": "jwt_token",
  "refresh": "refresh_token",
  "user": {
    "id": "uuid",
    "email": "jane@acme.com",
    "name": "Jane Smith",
    "role": "user"
  },
  "tenant": {
    "id": "uuid",
    "name": "Acme Corporation",
    "slug": "acme"
  }
}
```

---

## Local Frontend Changes

### ❌ REMOVE: Signup Page

The signup page should be removed from the local frontend since users cannot self-register.

**Files to Remove/Disable:**
- `local_frontend/src/components/auth/SignupForm.tsx`
- `local_frontend/src/pages/SignupPage.tsx`
- Navigation links to signup

### ✅ KEEP: Login Page (3-Field)

Login form should have:
- Tenant ID (slug)
- Email
- Password

**Example:**
```tsx
<form>
  <input name="tenant_id" placeholder="Company ID (e.g., acme)" />
  <input name="email" type="email" placeholder="Email" />
  <input name="password" type="password" placeholder="Password" />
  <button type="submit">Login</button>
</form>
```

### User Creation UI (Tenant Admin Only)

Add a "Users" management page in AdminView:
- List users in tenant
- Add user button (email, name, password, role)
- Edit user button
- Deactivate user button

**Permission Check:**
```tsx
const { isAdmin } = useAuthStore();

if (!isAdmin()) {
  return <PermissionDenied message="Only admins can manage users" />;
}
```

---

## Security Checks

### Tenant Creation Endpoint

```python
permission_classes = [IsSuperAdmin]

# IsSuperAdmin checks:
# 1. User is authenticated
# 2. User has is_superuser=True
# 3. Connection is on 'public' schema
```

### User Creation Endpoint

```python
permission_classes = [IsAuthenticated, IsAdminUser]

# IsAdminUser checks:
# 1. User is authenticated
# 2. User has role='admin'
```

### Login Endpoint

```python
# 1. Validates tenant_id (slug) exists
# 2. Validates email + password
# 3. Checks TenantMembership (user belongs to tenant)
# 4. Returns JWT with tenant_id and user_role in claims
```

---

## Example: Complete Onboarding Flow

### Step 1: Superadmin Creates Tenant

```bash
curl -X POST http://localhost:8000/api/v1/tenants/admin/tenants/ \
  -H "Authorization: Bearer {superadmin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TechStart Inc",
    "email": "contact@techstart.io",
    "admin_name": "Alice Johnson",
    "admin_email": "alice@techstart.io",
    "admin_password": "SuperSecret123!",
    "license_type": "pro",
    "company_size": "11-50",
    "industry": "SaaS"
  }'
```

**Response:**
```json
{
  "tenant": { ... },
  "admin_user": { ... },
  "domain": "techstart.agentverse.com",
  "message": "Tenant and admin user created successfully"
}
```

### Step 2: Tenant Admin Logs In

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "techstart",
    "email": "alice@techstart.io",
    "password": "SuperSecret123!"
  }'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": { "role": "admin", ... }
}
```

### Step 3: Tenant Admin Creates User

```bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Authorization: Bearer {tenant_admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "bob@techstart.io",
    "name": "Bob Smith",
    "password": "BobPassword456!",
    "role": "user"
  }'
```

**Response:**
```json
{
  "id": "uuid",
  "email": "bob@techstart.io",
  "name": "Bob Smith",
  "role": "user",
  "is_active": true
}
```

### Step 4: User Logs In

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "techstart",
    "email": "bob@techstart.io",
    "password": "BobPassword456!"
  }'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": { "role": "user", ... }
}
```

---

## Migration Notes

### For Existing Deployments

If you have existing tenants created via signup:
1. Designate one user as admin
2. Update their `role` to `'admin'` in database
3. Create `TenantMembership` records if missing

```sql
-- Promote user to admin
UPDATE users_user SET role = 'admin' WHERE email = 'existing@user.com';

-- Create membership if missing
INSERT INTO tenants_tenantmembership (tenant_id, user_id, role, is_active)
VALUES ('uuid', 'user_uuid', 'admin', true);
```

---

## Support

- **Superadmin Guide:** `SUPERADMIN_ANALYTICS_GUIDE.md`
- **API Reference:** `/api/v1/docs/` (Swagger)
- **Code:** `apps/tenants/views_admin.py`

---

**Version:** 1.0
**Status:** ✅ Ready for Implementation
