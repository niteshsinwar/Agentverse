# AgentVerse Service Abstraction Strategy

**Easy Migration from Free → Paid Services**

---

## 🎯 **Your Requirement:**

> "Currently choosing free services for budget, but should be able to easily switch later"

**Solution:** Abstract all external services behind interfaces so you can swap implementations with minimal code changes.

---

## 📊 **Current Setup (Free/Budget)**

| **Service** | **Free Option** | **Cost** | **Limitations** |
|-------------|----------------|----------|----------------|
| **Database** | PostgreSQL (Render) | $7/mo | 256MB RAM, 1GB storage |
| **Vector DB** | Qdrant (Self-hosted) | $0 | Manual management required |
| **Storage** | MinIO (Self-hosted) | $0 | Manual management required |
| **Deployment** | Render Free Tier | $0 | Sleeps after inactivity |
| **Redis** | Render Redis | $10/mo | 25MB |

**Total: ~$17/month**

---

## 🚀 **Future Migration Path (Paid/Production)**

| **Service** | **Paid Option** | **Cost** | **Benefits** |
|-------------|----------------|----------|--------------|
| **Database** | Render PostgreSQL Pro | $50/mo | 4GB RAM, 50GB storage, backups |
| **Vector DB** | Pinecone Serverless | $0.0002/query | Managed, auto-scaling |
| **Storage** | AWS S3 | $0.023/GB | 99.99% uptime, CDN integration |
| **Deployment** | Render Pro | $25/mo | Always on, auto-scaling |
| **Redis** | Render Redis Pro | $45/mo | 1GB, high availability |

**Total: ~$120-200/month (depends on usage)**

---

## 🏗️ **Abstraction Architecture**

### **Principle: Program to Interfaces, Not Implementations**

```python
# ❌ BAD: Hardcoded to specific service
from qdrant_client import QdrantClient

def store_embeddings(embeddings):
    client = QdrantClient(host="localhost", port=6333)  # ← Locked to Qdrant!
    client.upsert(...)


# ✅ GOOD: Abstract interface
class VectorStore(Protocol):
    """Interface - any vector DB can implement this"""
    def store_embeddings(self, embeddings: List[List[float]]) -> None: ...
    def search(self, query: List[float], limit: int) -> List[Dict]: ...

# Implementations
class QdrantVectorStore:  # Free option
    def store_embeddings(self, embeddings): ...
    def search(self, query, limit): ...

class PineconeVectorStore:  # Paid option
    def store_embeddings(self, embeddings): ...
    def search(self, query, limit): ...

# Usage - swap in ONE place
def get_vector_store() -> VectorStore:
    if settings.VECTOR_DB_PROVIDER == "qdrant":
        return QdrantVectorStore()
    elif settings.VECTOR_DB_PROVIDER == "pinecone":
        return PineconeVectorStore()
```

---

## 📋 **Service Abstraction Layer**

### **File: `cloud_backend/apps/core/services/abstractions.py`**

```python
"""
Service Abstractions - Swap implementations easily
"""
from typing import Protocol, List, Dict, Any
from dataclasses import dataclass

# ============================================================================
# VECTOR DATABASE ABSTRACTION
# ============================================================================

class VectorStore(Protocol):
    """Vector database interface - supports Qdrant, Pinecone, Weaviate, etc."""

    def create_collection(
        self,
        name: str,
        dimension: int,
        metadata: Dict[str, Any] = None
    ) -> None:
        """Create vector collection"""
        ...

    def store_embeddings(
        self,
        collection: str,
        embeddings: List[List[float]],
        documents: List[str],
        metadata: List[Dict[str, Any]]
    ) -> None:
        """Store embeddings with metadata"""
        ...

    def search(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 5,
        filter: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        ...

    def delete_collection(self, name: str) -> None:
        """Delete collection"""
        ...


# ============================================================================
# OBJECT STORAGE ABSTRACTION
# ============================================================================

class ObjectStorage(Protocol):
    """Object storage interface - supports MinIO, S3, GCS, etc."""

    def upload(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = None
    ) -> str:
        """
        Upload file.

        Returns:
            Public URL to file
        """
        ...

    def download(self, bucket: str, key: str) -> bytes:
        """Download file"""
        ...

    def delete(self, bucket: str, key: str) -> None:
        """Delete file"""
        ...

    def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        expiry: int = 3600
    ) -> str:
        """Generate temporary download URL"""
        ...

    def list_objects(
        self,
        bucket: str,
        prefix: str = ""
    ) -> List[Dict[str, Any]]:
        """List objects in bucket"""
        ...


# ============================================================================
# CACHE ABSTRACTION
# ============================================================================

class Cache(Protocol):
    """Cache interface - supports Redis, Memcached, etc."""

    def get(self, key: str) -> Any:
        """Get value"""
        ...

    def set(
        self,
        key: str,
        value: Any,
        ttl: int = None
    ) -> None:
        """Set value with optional TTL (seconds)"""
        ...

    def delete(self, key: str) -> None:
        """Delete key"""
        ...

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        ...

    def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        ...
```

---

## 🔄 **Implementation Examples**

### **1. Vector Database**

#### **File: `cloud_backend/apps/core/services/vector_db/qdrant.py`** (FREE)

```python
"""Qdrant implementation - FREE, self-hosted"""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

class QdrantVectorStore:
    """Free, self-hosted vector database"""

    def __init__(self, host: str, port: int):
        self.client = QdrantClient(host=host, port=port)

    def create_collection(self, name, dimension, metadata=None):
        self.client.recreate_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=dimension,
                distance=Distance.COSINE
            )
        )

    def store_embeddings(self, collection, embeddings, documents, metadata):
        points = [
            PointStruct(
                id=idx,
                vector=embedding,
                payload={
                    "document": doc,
                    **meta
                }
            )
            for idx, (embedding, doc, meta) in enumerate(
                zip(embeddings, documents, metadata)
            )
        ]
        self.client.upsert(collection_name=collection, points=points)

    def search(self, collection, query_vector, limit=5, filter=None):
        results = self.client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=limit,
            query_filter=filter
        )
        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload
            }
            for hit in results
        ]
```

#### **File: `cloud_backend/apps/core/services/vector_db/pinecone.py`** (PAID)

```python
"""Pinecone implementation - PAID, managed"""
from pinecone import Pinecone, ServerlessSpec

class PineconeVectorStore:
    """Managed vector database - easy to scale"""

    def __init__(self, api_key: str):
        self.pc = Pinecone(api_key=api_key)

    def create_collection(self, name, dimension, metadata=None):
        self.pc.create_index(
            name=name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )

    def store_embeddings(self, collection, embeddings, documents, metadata):
        index = self.pc.Index(collection)
        vectors = [
            {
                "id": str(idx),
                "values": embedding,
                "metadata": {
                    "document": doc,
                    **meta
                }
            }
            for idx, (embedding, doc, meta) in enumerate(
                zip(embeddings, documents, metadata)
            )
        ]
        index.upsert(vectors=vectors)

    def search(self, collection, query_vector, limit=5, filter=None):
        index = self.pc.Index(collection)
        results = index.query(
            vector=query_vector,
            top_k=limit,
            filter=filter,
            include_metadata=True
        )
        return [
            {
                "id": match.id,
                "score": match.score,
                "payload": match.metadata
            }
            for match in results.matches
        ]
```

---

### **2. Object Storage**

#### **File: `cloud_backend/apps/core/services/storage/minio.py`** (FREE)

```python
"""MinIO implementation - FREE, self-hosted S3-compatible"""
from minio import Minio

class MinIOStorage:
    """Free, self-hosted object storage"""

    def __init__(self, endpoint: str, access_key: str, secret_key: str):
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=True
        )

    def upload(self, bucket, key, data, content_type=None):
        from io import BytesIO
        self.client.put_object(
            bucket_name=bucket,
            object_name=key,
            data=BytesIO(data),
            length=len(data),
            content_type=content_type or "application/octet-stream"
        )
        return f"https://{self.client._endpoint_url}/{bucket}/{key}"

    def download(self, bucket, key):
        response = self.client.get_object(bucket, key)
        return response.read()

    def delete(self, bucket, key):
        self.client.remove_object(bucket, key)
```

#### **File: `cloud_backend/apps/core/services/storage/s3.py`** (PAID)

```python
"""AWS S3 implementation - PAID, managed"""
import boto3

class S3Storage:
    """Managed object storage with CDN integration"""

    def __init__(self, access_key: str, secret_key: str, region: str):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )

    def upload(self, bucket, key, data, content_type=None):
        self.s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=data,
            ContentType=content_type or "application/octet-stream"
        )
        return f"https://{bucket}.s3.amazonaws.com/{key}"

    def download(self, bucket, key):
        response = self.s3.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()

    def delete(self, bucket, key):
        self.s3.delete_object(Bucket=bucket, Key=key)

    def generate_presigned_url(self, bucket, key, expiry=3600):
        """CloudFront CDN URL (extra feature of S3)"""
        return self.s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expiry
        )
```

---

## ⚙️ **Configuration-Based Switching**

### **File: `cloud_backend/agentverse_cloud/settings.py`**

```python
"""Django settings - switch services via environment variables"""
import environ

env = environ.Env()

# Vector Database
VECTOR_DB_PROVIDER = env('VECTOR_DB_PROVIDER', default='qdrant')  # or 'pinecone'

if VECTOR_DB_PROVIDER == 'qdrant':
    VECTOR_DB_CONFIG = {
        'host': env('QDRANT_HOST', default='localhost'),
        'port': env.int('QDRANT_PORT', default=6333),
    }
elif VECTOR_DB_PROVIDER == 'pinecone':
    VECTOR_DB_CONFIG = {
        'api_key': env('PINECONE_API_KEY'),
    }

# Object Storage
STORAGE_PROVIDER = env('STORAGE_PROVIDER', default='minio')  # or 's3'

if STORAGE_PROVIDER == 'minio':
    STORAGE_CONFIG = {
        'endpoint': env('MINIO_ENDPOINT'),
        'access_key': env('MINIO_ACCESS_KEY'),
        'secret_key': env('MINIO_SECRET_KEY'),
    }
elif STORAGE_PROVIDER == 's3':
    STORAGE_CONFIG = {
        'access_key': env('AWS_ACCESS_KEY_ID'),
        'secret_key': env('AWS_SECRET_ACCESS_KEY'),
        'region': env('AWS_REGION', default='us-east-1'),
    }
```

---

## 🔧 **Service Factory (Dependency Injection)**

### **File: `cloud_backend/apps/core/services/factory.py`**

```python
"""Service factory - returns correct implementation based on config"""
from django.conf import settings
from .abstractions import VectorStore, ObjectStorage

def get_vector_store() -> VectorStore:
    """Get configured vector store implementation"""
    provider = settings.VECTOR_DB_PROVIDER

    if provider == 'qdrant':
        from .vector_db.qdrant import QdrantVectorStore
        return QdrantVectorStore(**settings.VECTOR_DB_CONFIG)

    elif provider == 'pinecone':
        from .vector_db.pinecone import PineconeVectorStore
        return PineconeVectorStore(**settings.VECTOR_DB_CONFIG)

    else:
        raise ValueError(f"Unknown vector DB provider: {provider}")


def get_object_storage() -> ObjectStorage:
    """Get configured object storage implementation"""
    provider = settings.STORAGE_PROVIDER

    if provider == 'minio':
        from .storage.minio import MinIOStorage
        return MinIOStorage(**settings.STORAGE_CONFIG)

    elif provider == 's3':
        from .storage.s3 import S3Storage
        return S3Storage(**settings.STORAGE_CONFIG)

    else:
        raise ValueError(f"Unknown storage provider: {provider}")
```

---

## 🎯 **Migration Process**

### **To Switch from Qdrant → Pinecone:**

**1. Update Environment Variables:**
```bash
# .env (before)
VECTOR_DB_PROVIDER=qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# .env (after)
VECTOR_DB_PROVIDER=pinecone
PINECONE_API_KEY=your-api-key-here
```

**2. Migrate Data:**
```bash
python manage.py migrate_vectors --from=qdrant --to=pinecone
```

**3. Restart Server:**
```bash
# That's it! No code changes needed
```

---

### **To Switch from MinIO → S3:**

**1. Update Environment Variables:**
```bash
# .env (before)
STORAGE_PROVIDER=minio
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# .env (after)
STORAGE_PROVIDER=s3
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
```

**2. Migrate Files:**
```bash
python manage.py migrate_storage --from=minio --to=s3
```

**3. Restart Server:**
```bash
# Done! All file uploads now go to S3
```

---

## 📊 **Cost Comparison**

### **Current (Free/Budget):**
```
PostgreSQL (Render): $7/mo
Qdrant (self-hosted): $0
MinIO (self-hosted): $0
Redis (Render): $10/mo
Render Free Tier: $0
─────────────────────
Total: $17/month
```

### **After Migration (Paid/Production):**
```
PostgreSQL Pro: $50/mo
Pinecone Serverless: ~$20/mo (pay per use)
AWS S3: ~$5/mo (pay per GB)
Redis Pro: $45/mo
Render Pro: $25/mo
─────────────────────
Total: ~$145/month
```

**ROI:** When you have 50+ paying customers at $20/mo = $1000/mo revenue
**Migration Cost:** ~2 hours of developer time + data migration

---

## ✅ **Benefits of Abstraction Approach:**

1. ✅ **No Code Changes** - Switch services by changing .env
2. ✅ **Type Safety** - Protocol ensures all implementations have same interface
3. ✅ **Easy Testing** - Mock services for unit tests
4. ✅ **Gradual Migration** - Can test new service before fully switching
5. ✅ **No Vendor Lock-in** - Can switch back if new service doesn't work

---

## 🚀 **Recommendation:**

**Start with:**
- Qdrant (free, self-hosted)
- MinIO (free, self-hosted)
- Render Free Tier

**When to upgrade:**
- **Qdrant → Pinecone:** When self-managing becomes burden (>10,000 queries/day)
- **MinIO → S3:** When need CDN, auto-scaling, or 99.99% uptime
- **Render Free → Pro:** When need always-on (not sleeping) + auto-scaling

**You'll know it's time when:**
- Managing infrastructure takes more than 5 hours/month
- Downtime affects paying customers
- Manual scaling becomes bottleneck

---

**BOTTOM LINE:** Your code is written to swap services easily. Start cheap, upgrade when revenue justifies it! 💰
