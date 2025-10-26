"""
Document Service
Handles document upload and processing workflow
"""
from typing import Dict, Any
import os

from src.core.document_processing.extractor import document_extractor
from src.core.document_processing.chunker import document_chunker
from src.core.document_processing.embedder import hybrid_embedder, text_embedder
from src.core.memory.vector_store import vector_store
from src.core.document_processing.storage import document_storage


class DocumentService:
    """
    Service for document processing workflow

    Responsibilities:
    - Coordinate document extraction, chunking, embedding pipeline
    - Store chunks in vector database
    - Store metadata in SQLite for UI
    - Handle errors gracefully
    """

    def __init__(self):
        """Initialize document service"""
        self.extractor = document_extractor
        self.chunker = document_chunker
        self.embedder = hybrid_embedder
        self.vector_store = vector_store
        self.storage = document_storage

    async def process_upload(
        self,
        file_content: bytes,
        filename: str,
        group_id: str,
        agent_id: str
    ) -> Dict[str, Any]:
        """
        Process document upload through MM-RAG pipeline

        Pipeline:
        1. Extract text content + detect modality
        2. Chunk content based on modality
        3. Generate embeddings (text or hybrid for images)
        4. Store chunks in vector database
        5. Store lightweight metadata in SQLite

        Args:
            file_content: Raw file bytes
            filename: Original filename
            group_id: Target group ID (hardcore filter)
            agent_id: Target agent ID

        Returns:
            {
                "success": bool,
                "document_id": str,
                "total_chunks": int,
                "modality": str,
                "error": Optional[str]
            }
        """
        temp_file_path = None

        try:
            # Emit telemetry - processing started
            from src.core.telemetry.events import emit_document_processing
            await emit_document_processing(
                group_id=group_id,
                agent_key=agent_id,
                filename=filename,
                status="start",
                meta={"file_size": len(file_content)}
            )

            # Notification already sent by endpoint - just process the document
            file_extension = os.path.splitext(filename)[1].lower()
            import tempfile

            # Step 1: Save to temporary file for processing
            with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name

            print(f"   [1/6] Smart routing - determining extraction method...")

            # SMART ROUTING: Pure text files → direct extraction, Everything else → Vision LLM
            PURE_TEXT_EXTENSIONS = {'.txt', '.md', '.py', '.js', '.ts', '.java', '.cpp', '.c',
                                   '.rb', '.go', '.rs', '.php', '.html', '.css', '.json', '.xml', '.yaml', '.yml'}

            if file_extension in PURE_TEXT_EXTENSIONS:
                print(f"         → Pure text file detected - using direct extraction")
                content, modality = await self.extractor.process_file(temp_file_path)
            else:
                print(f"         → Document/Image file detected - using Vision LLM")
                # Use Vision LLM for everything else (PDFs, DOCX, XLSX, images, etc.)
                modality = "vision"
                # Vision LLM will extract content in next step
                content = None

            print(f"         ✓ Routing: {'Direct extraction' if modality != 'vision' else 'Vision LLM'}")

            print(f"   [2/6] Extracting content (Vision LLM for documents/images)...")
            # Emit telemetry - extraction stage
            await emit_document_processing(
                group_id=group_id,
                agent_key=agent_id,
                filename=filename,
                status="extracting",
                meta={"modality": modality}
            )

            # Step 2: Get comprehensive content
            if modality == "vision":
                # Use Vision LLM for comprehensive extraction
                self.embedder._ensure_image_embedder()
                content = await self.embedder.image_embedder.get_image_description(temp_file_path)
                print(f"         ✓ Vision LLM extracted {len(content)} chars")
            elif not content:
                await emit_document_processing(
                    group_id=group_id,
                    agent_key=agent_id,
                    filename=filename,
                    status="error",
                    meta={"error": "Failed to extract content"}
                )
                return {
                    "success": False,
                    "error": "Failed to extract content from document",
                    "document_id": None,
                    "total_chunks": 0,
                    "modality": modality
                }

            print(f"   [3/6] Chunking content...")
            # Emit telemetry - chunking stage
            await emit_document_processing(
                group_id=group_id,
                agent_key=agent_id,
                filename=filename,
                status="chunking",
                meta={"content_length": len(content)}
            )

            # Step 3: Intelligent chunking (same for all types now)
            chunk_dicts = self.chunker.chunk_text(content, file_type=file_extension[1:])
            print(f"         ✓ Created {len(chunk_dicts)} chunks")

            print(f"   [4/6] Generating text embeddings...")
            # Emit telemetry - embedding stage
            await emit_document_processing(
                group_id=group_id,
                agent_key=agent_id,
                filename=filename,
                status="embedding",
                meta={"num_chunks": len(chunk_dicts)}
            )

            # Step 4: Generate text embeddings (universal pipeline)
            chunks = [chunk['text'] for chunk in chunk_dicts]
            text_embeddings = self.embedder.text_embedder.embed_texts(chunks)
            print(f"         ✓ Generated {len(text_embeddings)} text embeddings")

            print(f"   [5/6] Storing in ChromaDB vector database...")
            # Emit telemetry - storing stage
            await emit_document_processing(
                group_id=group_id,
                agent_key=agent_id,
                filename=filename,
                status="storing",
                meta={"num_embeddings": len(text_embeddings)}
            )
            # Step 5: Store in single text collection
            import time
            document_id = f"{group_id}_{agent_id}_{int(time.time() * 1000)}"

            # Get current conversation length for position-based decay
            from src.core.memory import session_store
            upload_message_number = len(session_store.get_history(group_id))

            # Prepare metadata for vector store (includes upload position for decay)
            chunk_metadata = {
                "group_id": group_id,
                "target_agent": agent_id,
                "filename": filename,
                "file_type": file_extension[1:],
                "modality": modality,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "upload_message_number": upload_message_number  # For position-based decay
            }

            # Universal storage - all documents go to text collection
            chunk_ids = self.vector_store.add_text_chunks(
                document_id=document_id,
                chunks=chunks,
                embeddings=text_embeddings,
                metadata=chunk_metadata
            )
            print(f"         ✓ Stored {len(chunk_ids)} chunks in text collection")

            print(f"   [6/6] Storing metadata in SQLite...")
            # Step 6: Store lightweight metadata in SQLite for UI
            file_size = len(file_content)
            total_chunks = len(chunk_dicts)

            self.storage.store_document_metadata(
                document_id=document_id,
                filename=filename,
                file_type=file_extension[1:],
                file_size=file_size,
                group_id=group_id,
                agent_id=agent_id,
                modality=modality,
                total_chunks=total_chunks,
                sender_type="user"
            )
            print(f"         ✓ Metadata stored in SQLite")

            # Emit telemetry - processing complete
            await emit_document_processing(
                group_id=group_id,
                agent_key=agent_id,
                filename=filename,
                status="complete",
                meta={
                    "document_id": document_id,
                    "total_chunks": total_chunks,
                    "modality": modality,
                    "file_size": file_size
                }
            )

            return {
                "success": True,
                "document_id": document_id,
                "total_chunks": total_chunks,
                "modality": modality,
                "error": None
            }

        except Exception as e:
            print(f"❌ Document processing failed: {e}")

            # Emit telemetry - processing error
            try:
                await emit_document_processing(
                    group_id=group_id,
                    agent_key=agent_id,
                    filename=filename,
                    status="error",
                    meta={"error": str(e)}
                )
            except:
                pass

            return {
                "success": False,
                "error": str(e),
                "document_id": None,
                "total_chunks": 0,
                "modality": "unknown"
            }

        finally:
            # Cleanup temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)


# Global instance
document_service = DocumentService()
