"""
RAG Service
Handles retrieval-augmented generation context retrieval
"""
from typing import List, Dict, Any, Tuple
from src.core.document_processing.embedder import text_embedder
from src.core.memory.vector_store import vector_store


class RAGService:
    """
    Service for RAG context retrieval (Text-Only, Simplified)

    Responsibilities:
    - Embed query text
    - Retrieve relevant chunks from vector store using semantic similarity
    - Format context for agent consumption
    """

    def __init__(self):
        """Initialize RAG service"""
        self.text_embedder = text_embedder
        self.vector_store = vector_store

    @property
    def settings(self):
        """Get fresh settings (supports hot-reload)"""
        from src.core.config.settings import get_settings
        return get_settings()

    async def retrieve_context(
        self,
        query: str,
        group_id: str,
        top_k: int = None
    ) -> str:
        """
        Retrieve RAG context for a query using semantic similarity

        Args:
            query: User query text
            group_id: Group ID (hardcore filter - only retrieve from this group)
            top_k: Number of chunks to retrieve (defaults to rag_top_k from settings)

        Returns:
            Formatted RAG context string ready for agent prompt injection
        """
        try:
            # Use settings if top_k not provided
            if top_k is None:
                top_k = getattr(self.settings, 'rag_top_k', 5)

            similarity_threshold = getattr(self.settings, 'rag_similarity_threshold', 0.5)

            print(f"🔍 RAG Retrieval for group {group_id}")
            print(f"   Query: {query[:100]}..." if len(query) > 100 else f"   Query: {query}")

            # Embed query text for semantic search
            try:
                text_embedding = self.text_embedder.embed_single(query)
                print(f"   ✓ Generated text query embedding ({self.settings.embedding_dimensions}d)")
            except Exception as embed_err:
                print(f"   ⚠️ Text embedding failed: {embed_err}")
                return ""

            # Load decay settings
            decay_enabled = getattr(self.settings, 'rag_decay_enabled', False)

            # Text-only search with similarity threshold (filters irrelevant results)
            # Similarity threshold from settings (default 0.35 = 35% minimum similarity)
            # This prevents "hi how r u" from matching CV documents
            print(f"   🔎 Searching vector database (top_{top_k * 2}, threshold={similarity_threshold})...")  # Get 2x for decay filtering
            chunks, metadatas, similarities = self.vector_store.search_text(
                query_embedding=text_embedding,
                group_id=group_id,
                top_k=top_k * 2,  # Retrieve more for decay re-ranking
                similarity_threshold=similarity_threshold,
                return_similarities=True  # Need similarities for decay calculation
            )

            # Apply position-based decay if enabled
            if decay_enabled and chunks:
                chunks, metadatas, similarities = self._apply_position_based_decay(
                    chunks, metadatas, similarities, group_id, similarity_threshold
                )

            # Format context
            if not chunks:
                print(f"   ⚠️ No relevant chunks found (all filtered by similarity threshold)")
                # Emit telemetry - no chunks found
                try:
                    from src.core.telemetry.events import emit_rag_retrieval
                    import asyncio
                    asyncio.create_task(emit_rag_retrieval(
                        group_id=group_id,
                        agent_key=None,
                        query=query,
                        chunks_found=0,
                        meta={"similarity_threshold": similarity_threshold, "top_k": top_k}
                    ))
                except:
                    pass
                return ""

            # Take top_k after decay re-ranking
            chunks = chunks[:top_k]
            metadatas = metadatas[:top_k]

            print(f"   ✅ Retrieved {len(chunks)} relevant chunks (passed similarity threshold)")
            for i, meta in enumerate(metadatas, 1):
                print(f"      {i}. {meta.get('filename', 'Unknown')} (chunk #{meta.get('chunk_index', '?')})")

            # Emit telemetry - successful retrieval
            try:
                from src.core.telemetry.events import emit_rag_retrieval
                import asyncio
                asyncio.create_task(emit_rag_retrieval(
                    group_id=group_id,
                    agent_key=None,
                    query=query,
                    chunks_found=len(chunks),
                    meta={
                        "similarity_threshold": similarity_threshold,
                        "top_k": top_k,
                        "decay_enabled": decay_enabled,
                        "documents": [meta.get('filename', 'Unknown') for meta in metadatas]
                    }
                ))
            except:
                pass

            context = self._format_context(chunks, metadatas)
            return context

        except Exception as e:
            import traceback
            print(f"⚠️ RAG retrieval failed: {e}")
            print(f"   Traceback: {traceback.format_exc()}")

            # Emit error telemetry
            try:
                from src.core.telemetry.events import emit_error
                import asyncio
                asyncio.create_task(emit_error(
                    group_id=group_id,
                    where="rag_service",
                    message=f"RAG retrieval failed: {str(e)}"
                ))
            except:
                pass

            return ""  # Graceful degradation - agent can still respond without RAG

    def _apply_position_based_decay(
        self,
        chunks: List[str],
        metadatas: List[Dict[str, Any]],
        similarities: List[float],
        group_id: str,
        similarity_threshold: float
    ) -> Tuple[List[str], List[Dict[str, Any]], List[float]]:
        """
        Apply conversation-position-based decay to document relevance

        Industry-standard formula (ArXiv 2509.19376, adapted for messages):
        score(q,d,m) = α * cos_sim(q,d) + (1-α) * decay_factor(m)
        decay_factor(m) = max(0.5^(messages_since/half_life), min_factor)

        Args:
            chunks: Retrieved chunks
            metadatas: Chunk metadata (contains upload_message_number)
            similarities: Cosine similarities from vector search
            group_id: Group ID for conversation length
            similarity_threshold: Re-filter after decay

        Returns:
            Re-ranked (chunks, metadatas, adjusted_similarities)
        """
        from src.core.memory import session_store

        # Load decay parameters
        alpha = getattr(self.settings, 'rag_decay_alpha', 0.7)
        half_life = getattr(self.settings, 'rag_decay_half_life_messages', 50)
        min_factor = getattr(self.settings, 'rag_decay_min_factor', 0.1)

        # Get current conversation length
        current_message_count = len(session_store.get_history(group_id))

        # Calculate decayed scores
        adjusted_results = []
        for chunk, meta, sim in zip(chunks, metadatas, similarities):
            upload_msg_num = meta.get('upload_message_number', current_message_count)  # Default to recent if missing
            messages_since = current_message_count - upload_msg_num

            # Half-life decay: 0.5^(messages_since / half_life)
            decay_factor = max(
                0.5 ** (messages_since / half_life),
                min_factor
            )

            # Fused score: α * semantic + (1-α) * recency
            adjusted_similarity = alpha * sim + (1 - alpha) * decay_factor

            # Re-filter by threshold after decay
            if adjusted_similarity >= similarity_threshold:
                adjusted_results.append((chunk, meta, adjusted_similarity, messages_since, decay_factor))

        # Sort by adjusted similarity (descending)
        adjusted_results.sort(key=lambda x: x[2], reverse=True)

        # Log decay details
        print(f"   📉 Position-based decay applied:")
        print(f"      α={alpha}, half_life={half_life} msgs, min_factor={min_factor}")
        print(f"      Current message count: {current_message_count}")
        for i, (_, meta, adj_sim, msg_since, decay) in enumerate(adjusted_results[:3], 1):
            orig_sim = similarities[chunks.index(_)] if _ in chunks else 0
            print(f"      {i}. {meta.get('filename', 'Unknown')}: msgs_since={msg_since}, "
                  f"decay={decay:.3f}, orig_sim={orig_sim:.3f} → adj_sim={adj_sim:.3f}")

        # Extract re-ranked results
        if not adjusted_results:
            return [], [], []

        ranked_chunks = [r[0] for r in adjusted_results]
        ranked_metas = [r[1] for r in adjusted_results]
        ranked_sims = [r[2] for r in adjusted_results]

        return ranked_chunks, ranked_metas, ranked_sims

    def _format_context(
        self,
        chunks: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> str:
        """
        Format retrieved chunks into readable context

        Args:
            chunks: Retrieved chunk texts
            metadatas: Chunk metadata (filename, agent, timestamp, etc.)

        Returns:
            Formatted context string
        """
        if not chunks:
            return ""

        context_parts = ["**RETRIEVED CONTEXT FROM GROUP DOCUMENTS:**\n"]

        for i, (chunk, meta) in enumerate(zip(chunks, metadatas), 1):
            filename = meta.get('filename', 'Unknown')
            file_type = meta.get('file_type', 'unknown')

            # Format chunk with minimal metadata (no technical details)
            context_parts.append(f"\n--- Document {i}: {filename} ---")
            context_parts.append(f"{chunk}\n")

        context_parts.append("\n**END OF RETRIEVED CONTEXT**\n")
        context_parts.append("Use the above context to answer the user's query naturally without exposing technical details.")

        return "\n".join(context_parts)


# Global instance
rag_service = RAGService()
