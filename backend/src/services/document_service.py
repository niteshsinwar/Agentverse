"""
Document Service
Handles document upload and processing workflow
"""
from typing import Dict, Any, Optional, List
import os

from src.core.document_processing.extractor import document_extractor
from src.core.document_processing.chunker import document_chunker
from src.core.document_processing.embedder import hybrid_embedder
from src.core.memory.vector_store import vector_store
from src.core.document_processing.storage import document_storage
from src.core.config.settings import get_settings


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
            settings = get_settings()
            supported_formats = getattr(settings, "supported_file_formats", []) or []
            allowed_extensions = {
                f".{ext.lower().lstrip('.')}"
                for ext in supported_formats
            }

            if allowed_extensions and file_extension not in allowed_extensions:
                raise RuntimeError(
                    f"File extension '{file_extension}' is not allowed. "
                    f"Supported types: {', '.join(sorted(allowed_extensions))}"
                )
            import tempfile

            # Step 1: Save to temporary file for processing
            with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name

            print(f"   [1/6] Smart routing - determining extraction method...")

            extracted_content, detected_modality, extraction_metadata = await self.extractor.process_file(
                temp_file_path,
                file_extension=file_extension
            )

            source_metadata = dict(extraction_metadata or {})
            raw_content = extracted_content if isinstance(extracted_content, str) else str(extracted_content)
            modality = detected_modality or "text"

            should_use_vision = False
            vision_reason: Optional[str] = None

            if file_extension in self.extractor.image_formats:
                should_use_vision = True
                vision_reason = "image_file"
                print("         → Image file detected - routing to Vision LLM")
            elif self._extraction_requires_vision(raw_content, modality, file_extension):
                should_use_vision = True
                vision_reason = "native_insufficient"
                print("         → Native parser suggested vision analysis (insufficient textual content)")
            else:
                print(f"         → Processed with native parser ({modality})")

            if should_use_vision:
                self.embedder._ensure_image_embedder()
                vision_content = await self.embedder.image_embedder.get_image_description(temp_file_path)
                content = vision_content
                modality = "vision"
                source_metadata.update({
                    "extraction_strategy": "vision_fallback",
                    "used_vision": True,
                    "vision_reason": vision_reason
                })
                print(f"         ✓ Vision LLM extracted {len(content)} chars")
            else:
                content = raw_content
                source_metadata.setdefault("extraction_strategy", source_metadata.get("summary_strategy", "native"))
                source_metadata["used_vision"] = False
                print(f"         ✓ Native parser extracted {len(content)} chars")

            source_metadata["content_length"] = len(content) if content else 0

            # Guardrails before chunking
            self._enforce_guardrails(
                content=content,
                metadata=source_metadata,
                settings=settings,
                filename=filename
            )

            print(f"         ✓ Routing: {'Vision LLM' if should_use_vision else 'Native extraction'}")

            print(f"   [2/6] Extracting content (Vision LLM for documents/images)...")
            await emit_document_processing(
                group_id=group_id,
                agent_key=agent_id,
                filename=filename,
                status="extracting",
                meta={
                    "modality": modality,
                    "used_vision": source_metadata.get("used_vision"),
                    "truncated": source_metadata.get("truncated"),
                    "row_count": source_metadata.get("row_count"),
                    "page_count": source_metadata.get("page_count")
                }
            )

            if not content or not str(content).strip():
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
            else:
                print(f"         ✓ Native parser extracted {len(content)} chars")

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
            def _serialize_value(value: Any) -> Any:
                if isinstance(value, (str, int, float, bool)) or value is None:
                    return value
                try:
                    import json
                    return json.dumps(value)
                except Exception:
                    return str(value)

            safe_processing_metadata = {
                key: _serialize_value(val)
                for key, val in (source_metadata or {}).items()
            }

            chunk_metadata = {
                "group_id": group_id,
                "target_agent": agent_id,
                "filename": filename,
                "file_type": file_extension[1:],
                "modality": modality,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "upload_message_number": upload_message_number,  # For position-based decay
                **{f"proc_{k}": v for k, v in safe_processing_metadata.items()}
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
                sender_type="user",
                metadata={
                    "document_id": document_id,
                    "file_extension": file_extension[1:],
                    "file_size": file_size,
                    "processing": source_metadata
                }
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
                    "file_size": file_size,
                    "truncated": source_metadata.get("truncated"),
                    "row_count": source_metadata.get("row_count"),
                    "page_count": source_metadata.get("page_count")
                }
            )

            await self._emit_processing_summary(
                group_id=group_id,
                agent_id=agent_id,
                filename=filename,
                document_id=document_id,
                metadata=source_metadata
            )

            return {
                "success": True,
                "document_id": document_id,
                "total_chunks": total_chunks,
                "modality": modality,
                "metadata": source_metadata,
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

            metadata_snapshot = locals().get("source_metadata")
            failure_message = f"❌ Document processing failed for {filename}: {str(e)}"
            try:
                from src.core.memory import session_store
                from src.core.telemetry.events import emit_message

                session_store.append_message(
                    group_id=group_id,
                    sender="system",
                    role="system",
                    content=failure_message,
                    metadata={
                        "message_type": "document_upload_failed",
                        "filename": filename,
                        "target_agent": agent_id,
                        "error": str(e)
                    }
                )
                await emit_message(
                    group_id,
                    sender="system",
                    role="system",
                    content=failure_message,
                    metadata={
                        "message_type": "document_upload_failed",
                        "filename": filename,
                        "target_agent": agent_id,
                        "error": str(e)
                    }
                )
            except Exception:
                pass

            return {
                "success": False,
                "error": str(e),
                "document_id": None,
                "total_chunks": 0,
                "modality": "unknown",
                "metadata": metadata_snapshot if isinstance(metadata_snapshot, dict) else None
            }

        finally:
            # Cleanup temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    async def _emit_processing_summary(
        self,
        group_id: str,
        agent_id: str,
        filename: str,
        document_id: str,
        metadata: Dict[str, Any]
    ) -> None:
        if not metadata:
            return

        summary_lines: List[str] = []

        if metadata.get("page_count"):
            summary_lines.append(f"• Detected {metadata['page_count']} pages.")

        if metadata.get("row_count") is not None:
            row_count = metadata.get("row_count")
            sampled = metadata.get("sampled_rows")
            if metadata.get("truncated"):
                summary_lines.append(
                    f"• Processed first {sampled} of approximately {row_count} rows for embeddings."
                )
            else:
                summary_lines.append(f"• Processed all {row_count} rows for embeddings.")

        if metadata.get("columns"):
            columns = metadata["columns"]
            if columns:
                display_cols = ", ".join(columns[:8])
                if len(columns) > 8:
                    display_cols += ", …"
                summary_lines.append(f"• Columns sampled: {display_cols}")

        if metadata.get("numeric_columns_profiled"):
            summary_lines.append(
                f"• Numeric stats generated for: {', '.join(metadata['numeric_columns_profiled'])}"
            )

        if metadata.get("notes"):
            summary_lines.append(f"• {metadata['notes']}")

        if not summary_lines:
            return

        summary_message = "📊 Document processed: {}\n{}".format(
            filename,
            "\n".join(summary_lines)
        )

        from src.core.memory import session_store
        from src.core.telemetry.events import emit_message

        message_metadata = {
            "message_type": "document_processing_summary",
            "document_id": document_id,
            "target_agent": agent_id,
            "processing_metadata": metadata
        }

        session_store.append_message(
            group_id=group_id,
            sender="system",
            role="system",
            content=summary_message,
            metadata=message_metadata
        )

        await emit_message(
            group_id,
            sender="system",
            role="system",
            content=summary_message,
            metadata=message_metadata
        )

    def _extraction_requires_vision(self, content: str, modality: str, file_extension: str) -> bool:
        """
        Determine if native extraction failed or produced low-value output,
        in which case we should fall back to the vision model.
        """
        if file_extension in self.extractor.image_formats:
            return True

        if not content or not content.strip():
            return True

        lowered = content.lower()
        failure_markers = [
            "error extracting",
            "unsupported file format",
            "unable to extract",
            "no readable content",
            "[image content detected",
            "[image detected"
        ]

        if any(marker in lowered for marker in failure_markers):
            return True

        if modality == "image":
            return True

        return False

    def _enforce_guardrails(
        self,
        content: str,
        metadata: Dict[str, Any],
        settings,
        filename: str
    ) -> None:
        """
        Refuse documents that exceed configured guardrails to prevent downstream crashes.
        """
        max_chars = getattr(settings, "max_document_characters", 200_000)
        max_rows = getattr(settings, "max_tabular_rows", 50_000)
        max_pages = getattr(settings, "max_pdf_pages", 200)

        content_length = metadata.get("content_length") or (len(content) if content else 0)
        if content_length and content_length > max_chars:
            raise ValueError(
                f"Document '{filename}' is too large to process safely "
                f"({content_length} characters > limit of {max_chars})."
            )

        row_count = metadata.get("row_count")
        if isinstance(row_count, int) and row_count > max_rows:
            raise ValueError(
                f"Tabular document '{filename}' has {row_count} rows which exceeds the limit of {max_rows}. "
                "Please trim the dataset before uploading."
            )

        page_count = metadata.get("page_count")
        if isinstance(page_count, int) and page_count > max_pages:
            raise ValueError(
                f"Document '{filename}' has {page_count} pages which exceeds the limit of {max_pages}. "
                "Please upload a smaller excerpt."
            )


# Global instance
document_service = DocumentService()
