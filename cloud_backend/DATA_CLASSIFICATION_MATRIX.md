# AgentVerse Cloud Backend - Complete Data Classification Matrix

**Date:** 2025-11-20
**Purpose:** Comprehensive mapping of all data types, storage locations, and access controls

---

## Data Classification Overview

| # | Data Type | Storage Schema | Tenant-Specific | Superadmin Access | Content Access |
|---|-----------|----------------|-----------------|-------------------|----------------|
| 1 | **Group** | Tenant Schema | ✅ Yes | Stats Only | ❌ NO Content |
| 2 | **Agent** | Tenant Schema | ✅ Yes | Stats Only | ❌ NO Config |
| 3 | **Tenant** | Public Schema | ❌ No | Full Access | ✅ Metadata Only |
| 4 | **Permission** | Tenant Schema | ✅ Yes | Stats Only | ✅ Metadata Only |
| 5 | **License** | Tenant Model | ❌ No | Full Access | ✅ YES |
| 6 | **Super Admin** | Public Schema | ❌ No | Full Access | ✅ YES |
| 7 | **Tenant Admin** | Tenant Schema | ✅ Yes | Stats Only | ❌ NO Data |
| 8 | **Tenant User** | Tenant Schema | ✅ Yes | Stats Only | ❌ NO Data |
| 9 | **MCP Server** | Tenant Schema | ✅ Yes | Stats Only | ❌ NO Config |
| 10 | **Tool** | Tenant Schema | ✅ Yes | Stats Only | ❌ NO Config |
| 11 | **Tenant Config** | Public Schema | ❌ No | Full Access | ✅ Metadata Only |
| 12 | **Conversation** | Tenant Schema | ✅ Yes | Stats Only | ❌ **NO MESSAGES** |
| 13 | **Documents** | Tenant Schema | ✅ Yes | Stats Only | ❌ **NO CONTENT** |
| 14 | **RAG/Embeddings** | Tenant Schema | ✅ Yes | Stats Only | ❌ **NO CONTENT** |

---

## 1. GROUP

### Storage
- **Schema:** Tenant Schema (e.g., `tenant_acme`)
- **Model:** `apps.groups.models.Group`
- **Database:** Isolated per tenant

### Data Fields
```python
- id (UUID)
- tenant (ForeignKey to Tenant)
- name (string)
- description (text)
- members (ManyToMany to User)
- created_by (UUID)
- created_at, updated_at (timestamps)
```

### Access Control

| Role | Can See | Can Modify |
|------|---------|------------|
| **Superadmin** | COUNT only via TenantStats | ❌ NO |
| **Tenant Admin** | All groups in their tenant | ✅ YES |
| **Tenant User** | Groups they're member of | Only their own |

### Superadmin Visibility
- ✅ `total_groups` (count) in TenantStats
- ✅ `active_groups_today` (count) in TenantStats
- ❌ Group names, descriptions, member lists

### API Endpoints
```
# Tenant-scoped
GET  /api/v1/groups/ (IsAuthenticated)
POST /api/v1/groups/ (IsAdminUser)

# Superadmin analytics
GET /api/v1/analytics/admin/tenant-stats/ → includes group counts
```

---

## 2. AGENT

### Storage
- **Schema:** Tenant Schema
- **Model:** `apps.agents.models.Agent`
- **Database:** Isolated per tenant

### Data Fields
```python
- id (UUID)
- tenant (ForeignKey to Tenant)
- name (string)
- description (text)
- emoji (string)
- llm_provider (choice: openai/anthropic/gemini/ollama)
- llm_model (string)
- system_prompt (text) ← SENSITIVE
- configuration (JSON) ← SENSITIVE
- created_by (UUID)
- created_at, updated_at
```

### Access Control

| Role | Can See | Can Modify |
|------|---------|------------|
| **Superadmin** | COUNT only via TenantStats | ❌ NO |
| **Tenant Admin** | All agents in tenant | ✅ YES |
| **Tenant User** | All agents in tenant | ❌ NO (read-only) |

### Superadmin Visibility
- ✅ `total_agents` (count) in TenantStats
- ✅ `new_agents_today` (count) in TenantStats
- ❌ Agent names, system prompts, configurations

### Why Superadmin CANNOT See Configurations
- System prompts may contain proprietary business logic
- Configurations may include API keys or sensitive parameters
- Tenant intellectual property protection

---

## 3. TENANT

### Storage
- **Schema:** Public Schema
- **Model:** `apps.tenants.models.Tenant`
- **Database:** Shared across all tenants

### Data Fields
```python
- id (UUID)
- name (string) ← Superadmin can see
- slug (string) ← Superadmin can see
- schema_name (string) ← Superadmin can see
- email (email) ← Superadmin can see
- admin_name (string) ← Superadmin can see
- phone (string) ← Superadmin can see
- company_size (choice) ← Superadmin can see
- industry (string) ← Superadmin can see
- license_type (choice) ← Superadmin can see
- subscription_status (choice) ← Superadmin can see
- storage_used_mb (integer) ← Superadmin can see
- messages_this_month (integer) ← Superadmin can see
- is_active (boolean) ← Superadmin can see
```

### Access Control

| Role | Can See | Can Modify |
|------|---------|------------|
| **Superadmin** | All tenants (full metadata) | ✅ YES (via admin) |
| **Tenant Admin** | Own tenant only | Limited fields |
| **Tenant User** | Own tenant only (read-only) | ❌ NO |

### Superadmin Full Access
- ✅ All tenant metadata
- ✅ Subscription management
- ✅ Suspend/activate tenants
- ✅ Update licenses

**Reason:** Tenants are platform-level entities, not user-created content.

---

## 4. PERMISSION

### Storage
- **Schema:** Tenant Schema
- **Model:** `apps.permissions.models.Permission`
- **Database:** Isolated per tenant

### Data Fields
```python
- id (UUID)
- tenant (ForeignKey to Tenant)
- subject (choice: user/group)
- subject_id (UUID)
- resource (choice: agent/tool/mcp/group/document)
- resource_id (UUID)
- action (choice: read/write/execute/manage)
- granted (boolean)
- created_at
```

### Access Control

| Role | Can See | Can Modify |
|------|---------|------------|
| **Superadmin** | COUNT only via TenantStats | ❌ NO |
| **Tenant Admin** | All permissions in tenant | ✅ YES |
| **Tenant User** | Own permissions only | ❌ NO |

### Superadmin Visibility
- ✅ COUNT of permissions (future TenantStats field)
- ❌ Permission details (who has access to what)

**Why:** Permission details reveal tenant's internal access control policies.

---

## 5. LICENSE

### Storage
- **Schema:** Public Schema (Tenant.license_type field)
- **Model:** Settings constant (LICENSE_TIERS)
- **Database:** Configuration file

### Data Fields
```python
# In Tenant model:
- license_type (choice: free/pro/enterprise)
- license_limits (JSON):
  {
    "max_users": 10,
    "max_agents": 5,
    "max_storage_mb": 1000,
    "max_messages_per_month": 10000
  }
```

### Access Control

| Role | Can See | Can Modify |
|------|---------|------------|
| **Superadmin** | All license info | ✅ YES |
| **Tenant Admin** | Own license info | ❌ NO (read-only) |
| **Tenant User** | Nothing | ❌ NO |

### Superadmin Full Access
- ✅ View all licenses
- ✅ Upgrade/downgrade licenses
- ✅ Set custom limits
- ✅ View license tier distribution (analytics)

---

## 6. SUPER ADMIN

### Storage
- **Schema:** Public Schema
- **Model:** `apps.users.models.User` (with is_superuser=True)
- **Database:** Shared (SHARED_APPS)

### Data Fields
```python
- id (UUID)
- email (email)
- name (string)
- is_superuser (boolean) = True
- is_staff (boolean) = True
- role (string) = 'admin'
```

### Access Control

| Role | Can See | Can Modify |
|------|---------|------------|
| **Superadmin** | All superadmins | ✅ YES (via Django admin) |
| **Tenant Admin** | Nothing | ❌ NO |
| **Tenant User** | Nothing | ❌ NO |

### Superadmin Full Access
- ✅ Manage other superadmins
- ✅ Access Django admin panel
- ✅ Access all analytics endpoints

---

## 7. TENANT ADMIN

### Storage
- **Schema:** Tenant Schema (but User model in SHARED_APPS)
- **Model:** `apps.users.models.User` (with role='admin')
- **Link:** `apps.tenants.models.TenantMembership`

### Data Fields
```python
# User model:
- id (UUID)
- email (email)
- name (string)
- role (string) = 'admin'
- is_active (boolean)

# TenantMembership:
- tenant (ForeignKey to Tenant)
- user (ForeignKey to User)
- role (string) = 'admin'
- is_active (boolean)
```

### Access Control

| Role | Can See | Can Modify |
|------|---------|------------|
| **Superadmin** | COUNT only via TenantStats | ❌ NO personal data |
| **Tenant Admin** | All users in their tenant | ✅ YES |
| **Tenant User** | Other users (basic info) | ❌ NO |

### Superadmin Visibility
- ✅ `total_users` (count including admins)
- ✅ Contact email in Tenant model
- ❌ Individual user data, emails, names

---

## 8. TENANT USER

### Storage
- **Schema:** Tenant Schema (User model in SHARED_APPS)
- **Model:** `apps.users.models.User` (with role='user')
- **Link:** `apps.tenants.models.TenantMembership`

### Data Fields
```python
# User model:
- id (UUID)
- email (email)
- name (string)
- role (string) = 'user'
- is_active (boolean)
- last_login_at (timestamp)
```

### Access Control

| Role | Can See | Can Modify |
|------|---------|------------|
| **Superadmin** | COUNT only via TenantStats | ❌ NO personal data |
| **Tenant Admin** | All users in tenant | ✅ YES |
| **Tenant User** | Other users (basic info) | ❌ NO |

### Superadmin Visibility
- ✅ `total_users`, `active_users_today`, `new_users_today` (counts)
- ❌ Individual user data (names, emails, activity logs)

---

## 9. MCP SERVER

### Storage
- **Schema:** Tenant Schema
- **Model:** `apps.mcp.models.MCPServer`
- **Database:** Isolated per tenant

### Data Fields
```python
- id (UUID)
- tenant (ForeignKey to Tenant)
- name (string)
- description (text)
- url (URL) ← SENSITIVE
- api_key (encrypted) ← VERY SENSITIVE
- configuration (JSON) ← SENSITIVE
- created_by (UUID)
- created_at, updated_at
```

### Access Control

| Role | Can See | Can Modify |
|------|---------|------------|
| **Superadmin** | COUNT only via TenantStats | ❌ NO |
| **Tenant Admin** | All MCP servers in tenant | ✅ YES |
| **Tenant User** | All MCP servers (masked keys) | ❌ NO |

### Superadmin Visibility
- ✅ `total_mcp_servers` (count) in TenantStats
- ❌ MCP URLs, API keys, configurations

**Why Superadmin CANNOT See:**
- API keys are extremely sensitive
- Configurations may contain proprietary integration logic
- URLs may reveal internal infrastructure

---

## 10. TOOL

### Storage
- **Schema:** Tenant Schema
- **Model:** `apps.tools.models.Tool`
- **Database:** Isolated per tenant

### Data Fields
```python
- id (UUID)
- tenant (ForeignKey to Tenant)
- name (string)
- description (text)
- code (text) ← VERY SENSITIVE
- parameters (JSON) ← SENSITIVE
- created_by (UUID)
- created_at, updated_at
```

### Access Control

| Role | Can See | Can Modify |
|------|---------|------------|
| **Superadmin** | COUNT only via TenantStats | ❌ NO |
| **Tenant Admin** | All tools in tenant | ✅ YES |
| **Tenant User** | All tools (read-only) | ❌ NO |

### Superadmin Visibility
- ✅ `total_tools` (count) in TenantStats
- ❌ Tool code, parameters, configurations

**Why Superadmin CANNOT See:**
- Tool code contains proprietary business logic
- May include API integrations with sensitive credentials
- Intellectual property protection

---

## 11. TENANT CONFIG (TenantSettings)

### Storage
- **Schema:** Public Schema
- **Model:** `apps.tenants.models.TenantSettings`
- **Database:** Shared (OneToOne with Tenant)

### Data Fields
```python
- id (UUID)
- tenant (OneToOne to Tenant)
- logo_url (URL) ← Superadmin can see
- primary_color (string) ← Superadmin can see
- company_website (URL) ← Superadmin can see
- features_enabled (JSON) ← Superadmin can see
- notifications_enabled (boolean) ← Superadmin can see
- integrations (JSON) ← MAY CONTAIN SENSITIVE DATA
- custom_settings (JSON) ← MAY CONTAIN SENSITIVE DATA
```

### Access Control

| Role | Can See | Can Modify |
|------|---------|------------|
| **Superadmin** | Metadata only (logo, colors) | ❌ NO |
| **Tenant Admin** | All settings | ✅ YES |
| **Tenant User** | All settings (read-only) | ❌ NO |

### Superadmin Visibility
- ✅ Branding (logo, colors, website)
- ✅ Feature flags (boolean toggles)
- ⚠️ Integrations (depends on content - may need filtering)
- ❌ Custom settings (may contain sensitive data)

---

## 12. CONVERSATION HISTORY

### Storage
- **Schema:** Tenant Schema
- **Model:** `apps.messages.models.Message` (assumed)
- **Database:** Isolated per tenant

### Data Fields
```python
- id (UUID)
- tenant (ForeignKey to Tenant)
- group (ForeignKey to Group)
- agent (ForeignKey to Agent)
- user (ForeignKey to User)
- content (text) ← EXTREMELY SENSITIVE
- role (choice: user/assistant/system)
- created_at (timestamp)
```

### Access Control

| Role | Can See | Can Modify |
|------|---------|------------|
| **Superadmin** | COUNT only via TenantStats | ❌ **ABSOLUTELY NO** |
| **Tenant Admin** | All messages in tenant | ✅ YES (view/delete) |
| **Tenant User** | Messages in their groups | ❌ NO (view only) |

### Superadmin Visibility
- ✅ `messages_sent_today` (count)
- ✅ `total_messages` (count)
- ❌ **ZERO access to message content**

**Why Superadmin CANNOT See:**
- **Privacy:** Messages contain user conversations
- **Compliance:** May include PII, HIPAA, GDPR-protected data
- **Trust:** Fundamental privacy promise to tenants

### Critical Security Rule
```python
# NEVER allow superadmin to query Message.content
# ONLY aggregate counts in TenantStats
```

---

## 13. DOCUMENTS

### Storage
- **Schema:** Tenant Schema
- **Model:** `apps.documents.models.Document`
- **Database:** Isolated per tenant
- **Files:** Object storage (S3/MinIO) with tenant prefix

### Data Fields
```python
- id (UUID)
- tenant (ForeignKey to Tenant)
- group (ForeignKey to Group)
- filename (string)
- file_path (string) ← Path to S3/storage
- file_size (integer)
- mime_type (string)
- content (text or file) ← EXTREMELY SENSITIVE
- uploaded_by (UUID)
- created_at
```

### Access Control

| Role | Can See | Can Modify |
|------|---------|------------|
| **Superadmin** | COUNT, SIZE only via TenantStats | ❌ **ABSOLUTELY NO** |
| **Tenant Admin** | All documents in tenant | ✅ YES |
| **Tenant User** | Documents in their groups | ❌ NO (view only) |

### Superadmin Visibility
- ✅ `documents_uploaded_today` (count)
- ✅ `total_documents` (count)
- ✅ `storage_used_mb` (aggregate size)
- ❌ **ZERO access to document content**
- ❌ Document filenames (may reveal sensitive info)
- ❌ Document paths (security risk)

**Why Superadmin CANNOT See:**
- **Privacy:** Documents may contain sensitive business data
- **Compliance:** May include contracts, financial records, PII
- **Security:** Filenames alone can reveal confidential information
- **Trust:** Core privacy guarantee to tenants

---

## 14. RAG / EMBEDDINGS

### Storage
- **Schema:** Tenant Schema
- **Model:** `apps.rag.models.Embedding` (assumed) or Vector DB
- **Database:** Isolated per tenant + Vector DB (Pinecone/Weaviate/Chroma)

### Data Fields
```python
# Metadata in SQL:
- id (UUID)
- tenant (ForeignKey to Tenant)
- document (ForeignKey to Document)
- chunk_text (text) ← SENSITIVE
- chunk_index (integer)
- created_at

# Vector in Vector DB:
- embedding_id (UUID)
- vector (float array)
- metadata (JSON with tenant_id, document_id)
```

### Access Control

| Role | Can See | Can Modify |
|------|---------|------------|
| **Superadmin** | COUNT only (future TenantStats) | ❌ **ABSOLUTELY NO** |
| **Tenant Admin** | All embeddings in tenant | ✅ YES (regenerate) |
| **Tenant User** | Nothing (used by agents) | ❌ NO |

### Superadmin Visibility
- ✅ `total_embeddings` (count) - future stat
- ✅ `embedding_storage_mb` (size) - future stat
- ❌ **ZERO access to chunk text**
- ❌ Vector data
- ❌ Source document references

**Why Superadmin CANNOT See:**
- **Privacy:** Chunks contain original document text
- **Security:** Embeddings can be reverse-engineered to reveal content
- **Compliance:** Subject to same rules as source documents

### Vector DB Security
```python
# Ensure vector DB queries include tenant_id filter
# Example (Pinecone):
index.query(
    vector=query_embedding,
    filter={"tenant_id": {"$eq": tenant_id}},  # CRITICAL
    top_k=10
)
```

---

## SECURITY SUMMARY

### Superadmin Access Levels

#### ✅ FULL ACCESS (Metadata & Management)
1. Tenant (company info, subscriptions)
2. License (tiers, limits)
3. Super Admin (manage other superadmins)
4. TenantSettings (branding, features)

#### ✅ STATISTICS ONLY (Counts & Aggregates)
5. Groups (total_groups, active_groups_today)
6. Agents (total_agents, new_agents_today)
7. Tenant Admins (included in total_users count)
8. Tenant Users (total_users, active_users_today)
9. MCP Servers (total_mcp_servers)
10. Tools (total_tools)
11. Conversations (messages_sent_today, total_messages)
12. Documents (documents_uploaded_today, storage_used_mb)
13. RAG (future: total_embeddings count)

#### ❌ ZERO ACCESS (Privacy-Protected)
- Agent configurations & system prompts
- MCP server URLs & API keys
- Tool code & parameters
- **Message content** (CRITICAL)
- **Document content** (CRITICAL)
- **RAG chunk text** (CRITICAL)
- Permission details
- User personal data (names, emails beyond contact)

---

## COMPLIANCE & PRIVACY

### Data Protection Principles

1. **Aggregate-Only Analytics**
   - Superadmin sees "how many" not "what"
   - Example: "1,234 messages today" ✅ vs "User said: Hello" ❌

2. **No PII Access**
   - Superadmin cannot see user emails (except tenant contact)
   - Cannot see user activity logs
   - Cannot see user-created content

3. **No Content Access**
   - Messages, documents, RAG chunks are strictly off-limits
   - Even metadata like filenames are restricted
   - Configuration files may contain secrets

4. **Tenant Isolation Enforcement**
   - All tenant-specific data in separate schemas
   - Cross-tenant queries blocked by design
   - Vector DB queries must include tenant_id filter

### Audit Trail

All superadmin actions should be logged:
- Who accessed what endpoint
- When tenant was created/modified
- When tickets were assigned/resolved
- When subscriptions were changed

---

## IMPLEMENTATION CHECKLIST

### ✅ Completed

- [x] TenantStats model (aggregate counts)
- [x] GlobalPlatformStats model (platform metrics)
- [x] SupportTicket model (tenant support)
- [x] IsSuperAdmin permission class
- [x] Superadmin analytics viewsets
- [x] Superadmin tenant management
- [x] Django admin interfaces
- [x] Documentation (this file)

### 🔄 To Verify

- [ ] All tenant-specific models have `tenant` ForeignKey
- [ ] All admin classes use TenantFilteredAdmin (where needed)
- [ ] Vector DB queries include tenant_id filter
- [ ] API endpoints enforce proper permissions
- [ ] No message/document content endpoints for superadmin

### 📋 Future Enhancements

- [ ] Add Permission count to TenantStats
- [ ] Add RAG embedding counts to TenantStats
- [ ] Add automated daily stats calculation (Celery task)
- [ ] Add audit logging for superadmin actions
- [ ] Add data export (CSV) for analytics
- [ ] Add alerting for at-risk tenants

---

**Version:** 1.0
**Last Updated:** 2025-11-20
**Status:** ✅ Complete Reference Guide
