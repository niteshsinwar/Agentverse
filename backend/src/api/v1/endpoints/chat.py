"""
Chat API Endpoints
RESTful endpoints for chat and messaging functionality
"""

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from typing import List, Dict, Any, Optional
import os

from src.services.orchestrator_service import OrchestratorService
from src.api.v1.models.chat import SendMessageRequest, MessageResponse
from src.api.v1.dependencies import get_orchestrator_service

router = APIRouter()


@router.get("/groups/{group_id}/messages", response_model=List[MessageResponse])
async def get_group_messages(
    group_id: str,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Get message history for a group.

    Returns all messages in a group's conversation history.
    """
    try:
        messages = service.get_group_messages(group_id)

        # Sanitize metadata to avoid exposing private document fields to the UI.
        private_keys = {"extracted_content", "original_prompt", "content_summary"}

        sanitized = []
        for i, msg in enumerate(messages):
            md = msg.get("metadata") or {}
            safe_md = {k: v for k, v in md.items() if k not in private_keys}

            sanitized.append(
                MessageResponse(
                    id=i,
                    group_id=group_id,
                    sender=msg["sender"],
                    role=msg["role"],
                    content=msg["content"],
                    metadata=safe_md,
                    created_at=msg["created_at"]
                )
            )

        return sanitized
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")


@router.post("/groups/{group_id}/messages")
async def send_message(
    group_id: str,
    request: SendMessageRequest,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Send a message to a group.

    Processes a user message and routes it to the appropriate agents.
    """
    try:
        # Format message for agent routing
        message = request.message

        # Check if this is a single-agent group
        group_agents = service.list_group_agents(group_id)

        if len(group_agents) == 1:
            # Single agent - no @mention needed
            pass
        else:
            # Multiple agents - add @mention if not present
            if not message.strip().startswith(f"@{request.agent_id}"):
                message = f"@{request.agent_id} {message}"

        print(f"🚀 Processing message for group {group_id}: {message[:100]}...")

        await service.process_message(group_id, message)

        print(f"✅ Message processed successfully for group {group_id}")
        return {"message": "Message sent successfully"}

    except Exception as e:
        print(f"❌ Message processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.get("/groups/{group_id}/documents")
async def get_group_documents(
    group_id: str,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Get documents uploaded to a group.

    Returns all documents that have been uploaded to the group.
    """
    try:
        documents = service.get_group_documents(group_id)
        result = []

        for doc in documents:
            md = doc.get('metadata', {})
            filename = md.get('filename', 'Unknown')
            sender = doc.get('sender', 'Unknown')
            target = md.get('target_agent', 'Unknown')
            size = md.get('file_size', 0)

            # Format file size
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"

            # Format date
            import datetime
            date_str = datetime.datetime.fromtimestamp(
                doc.get('created_at', 0)
            ).strftime("%Y-%m-%d %H:%M")

            # Sanitize metadata before returning to UI: do not include extracted content or original prompt
            result.append({
                "document_id": md.get('document_id', ''),
                "filename": filename,
                "sender": sender,
                "target_agent": target,
                "size": size,
                "size_str": size_str,
                "date_str": date_str,
                "created_at": doc.get('created_at', 0),
                "file_extension": md.get('file_extension', ''),
                # Keep only a short public summary if present; otherwise omit private fields
                "content_summary": md.get('content_summary', '') if md.get('content_summary') else None
            })

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get documents: {str(e)}")


@router.post("/groups/{group_id}/documents/upload/")
async def upload_document(
    group_id: str,
    file: UploadFile = File(...),
    agent_id: str = Form(...),
    message: Optional[str] = Form(""),
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Upload a document to a group and process it with a specific agent.

    The document will be processed by the specified agent and integrated into the conversation.
    """
    try:
        # Validate file size (10MB limit)
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        file_content = await file.read()

        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size ({len(file_content)} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE} bytes)"
            )

        # Validate file extension
        allowed_extensions = {'.txt', '.md', '.pdf', '.docx', '.csv', '.json', '.py', '.js', '.ts', '.html', '.css', '.png'}
        file_extension = os.path.splitext(file.filename)[1].lower()

        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File extension '{file_extension}' is not allowed. Supported: {', '.join(allowed_extensions)}"
            )

        # Reset file pointer
        await file.seek(0)

        # Process the document upload through the orchestrator
        result = await service.process_document_upload(
            group_id=group_id,
            agent_id=agent_id,
            file=file,
            message=message or f"Please analyze this uploaded document: {file.filename}"
        )

        # Return minimal info to caller - do not expose extracted content or summaries
        return {
            "message": "Document uploaded and processed successfully",
            "document_id": result.get("document_id"),
            "filename": file.filename,
            "agent_id": agent_id,
            "file_size": len(file_content)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")