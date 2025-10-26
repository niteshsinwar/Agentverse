"""
Multi-Modal Vector Store
Separate collections for text and images with fusion search
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional, Tuple


class MultiModalVectorStore:
    """
    Manages two vector collections:
    1. Text collection (OpenAI embeddings, 1536 dims)
    2. Image collection (CLIP embeddings, 512 dims)

    Provides fusion search across both modalities
    """

    def __init__(self, persist_directory: str = "chroma_db"):
        """
        Initialize ChromaDB with provider-specific collections

        ENTERPRISE DESIGN: Each embedding provider gets its own collection
        to avoid dimension mismatches and allow seamless provider switching.

        Collection naming: text_chunks_{provider}_{model}_{dimensions}
        Example: text_chunks_openai_text-embedding-3-small_1536
        """
        # Use PersistentClient for disk persistence (not ephemeral Client)
        # Store at backend root level alongside agent_store, data, documents
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Load current embedding configuration
        from src.core.config.settings import get_settings
        self.settings = get_settings()

        # Generate provider-specific collection names
        # This allows multiple providers to coexist without conflicts
        provider = self.settings.embedding_provider
        model = self.settings.embedding_model.replace("/", "_").replace("-", "_")
        dimensions = self.settings.embedding_dimensions

        text_collection_name = f"text_chunks_{provider}_{model}_{dimensions}"

        # Text collection with provider-specific naming
        # IMPORTANT: Collection name includes provider/model/dims to prevent conflicts
        self.text_collection = self.client.get_or_create_collection(
            name=text_collection_name,
            metadata={
                "hnsw:space": "cosine",
                "embedding_provider": provider,
                "embedding_model": self.settings.embedding_model,
                "embedding_dimensions": str(dimensions)
            }
        )

        # SIMPLIFIED: No image collection - all embeddings are text-based
        # Images are processed with vision LLM → text → text embeddings
        # Single unified collection for all document types

        print(f"📊 Using ChromaDB collection:")
        print(f"   {text_collection_name} ({self.text_collection.count()} docs)")

    def add_text_chunks(
        self,
        document_id: str,
        chunks: List[str],
        embeddings: List[List[float]],
        metadata: Dict[str, Any]
    ) -> List[str]:
        """Add text document chunks to text collection"""
        chunk_ids = []
        chunk_metadatas = []

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{document_id}_chunk_{i}"
            chunk_ids.append(chunk_id)

            chunk_metadata = {
                **metadata,
                "chunk_index": i,
                "document_id": document_id
            }
            chunk_metadatas.append(chunk_metadata)

        self.text_collection.add(
            ids=chunk_ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=chunk_metadatas
        )

        return chunk_ids

    def add_image_chunks(
        self,
        document_id: str,
        descriptions: List[str],
        text_embeddings: List[List[float]],
        metadata: Dict[str, Any]
    ) -> List[str]:
        """
        Add image chunks (SIMPLIFIED: text embeddings only, no CLIP)
        Images are stored the same way as text documents

        Args:
            document_id: Unique document ID
            descriptions: Vision LLM descriptions of images
            text_embeddings: Text embeddings of descriptions
            metadata: Document metadata

        Returns:
            List of chunk IDs
        """
        # Store in text collection only (same as text documents)
        return self.add_text_chunks(document_id, descriptions, text_embeddings, metadata)

    def search_text(
        self,
        query_embedding: List[float],
        group_id: str,
        top_k: int = 5,
        similarity_threshold: float = 0.5,
        return_similarities: bool = False
    ) -> Tuple[List[str], List[Dict[str, Any]], Optional[List[float]]]:
        """
        Search text collection with similarity threshold filtering

        Args:
            similarity_threshold: Minimum cosine similarity (0-1). Default 0.5.
                                 Only return chunks with similarity >= threshold.
                                 This prevents irrelevant results like "hi how r u"
                                 matching with CV documents.
            return_similarities: If True, return similarity scores (for decay calculation)

        Returns:
            (chunks, metadatas, similarities) if return_similarities=True
            (chunks, metadatas, None) if return_similarities=False
        """
        results = self.text_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"group_id": {"$eq": group_id}}
        )

        if not results['documents'] or len(results['documents']) == 0:
            return [], [], [] if return_similarities else None

        # Filter by similarity threshold (convert distance to similarity)
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        distances = results['distances'][0]  # ChromaDB returns cosine distances

        filtered_docs = []
        filtered_metas = []
        filtered_sims = []

        for doc, meta, distance in zip(documents, metadatas, distances):
            # Convert distance to similarity: similarity = 1 - distance (for cosine)
            similarity = 1.0 - distance

            if similarity >= similarity_threshold:
                filtered_docs.append(doc)
                filtered_metas.append(meta)
                if return_similarities:
                    filtered_sims.append(similarity)
            else:
                print(f"   ⏭️  Filtered out chunk (similarity: {similarity:.3f} < {similarity_threshold})")

        if return_similarities:
            return filtered_docs, filtered_metas, filtered_sims
        else:
            return filtered_docs, filtered_metas, None

    def delete_document(self, document_id: str) -> None:
        """Delete document from text collection"""
        self.text_collection.delete(where={"document_id": {"$eq": document_id}})

    def delete_group(self, group_id: str) -> None:
        """Delete all group documents from text collection"""
        self.text_collection.delete(where={"group_id": {"$eq": group_id}})

    def check_provider_compatibility(self) -> Dict[str, Any]:
        """
        Check if current embedding provider matches stored documents

        Returns:
            {
                "compatible": bool,
                "stored_provider": str,
                "stored_model": str,
                "stored_dimensions": int,
                "current_provider": str,
                "current_model": str,
                "current_dimensions": int,
                "warning": str (if incompatible)
            }
        """
        # Get collection metadata
        collection_metadata = self.text_collection.metadata

        stored_provider = collection_metadata.get("embedding_provider", "unknown")
        stored_model = collection_metadata.get("embedding_model", "unknown")
        stored_dimensions = int(collection_metadata.get("embedding_dimensions", 0))

        current_provider = self.settings.embedding_provider
        current_model = self.settings.embedding_model
        current_dimensions = self.settings.embedding_dimensions

        # Check compatibility
        compatible = (
            stored_provider == current_provider and
            stored_model == current_model and
            stored_dimensions == current_dimensions
        )

        # Check if collection has any documents
        collection_count = self.text_collection.count()
        has_documents = collection_count > 0

        result = {
            "compatible": compatible,
            "has_documents": has_documents,
            "document_count": collection_count,
            "stored_provider": stored_provider,
            "stored_model": stored_model,
            "stored_dimensions": stored_dimensions,
            "current_provider": current_provider,
            "current_model": current_model,
            "current_dimensions": current_dimensions,
            "warning": None
        }

        # With provider-specific collections, incompatibility is impossible
        # But we still show this for legacy collections without metadata
        if not compatible and has_documents:
            result["warning"] = (
                f"ℹ️ PROVIDER-SPECIFIC COLLECTIONS INFO\n\n"
                f"You have {collection_count} documents in this collection.\n"
                f"Switching providers will create a separate collection.\n\n"
                f"Current: {current_provider}/{current_model} ({current_dimensions}d)\n"
                f"Stored: {stored_provider}/{stored_model} ({stored_dimensions}d)\n\n"
                f"✅ No data loss: Each provider maintains its own documents.\n"
                f"📊 All collections are preserved and searchable."
            )

        # List all available collections
        all_collections = []
        try:
            for collection in self.client.list_collections():
                if collection.name.startswith("text_chunks_"):
                    col_metadata = collection.metadata or {}
                    all_collections.append({
                        "name": collection.name,
                        "provider": col_metadata.get("embedding_provider", "unknown"),
                        "model": col_metadata.get("embedding_model", "unknown"),
                        "dimensions": col_metadata.get("embedding_dimensions", "unknown"),
                        "count": collection.count()
                    })
            result["all_collections"] = all_collections
        except:
            result["all_collections"] = []

        return result


# Global instance
vector_store = MultiModalVectorStore()
