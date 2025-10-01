"""
Chat API Endpoints
RESTful endpoints for chat and messaging functionality
"""

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import os
import json
import asyncio

from src.services.orchestrator_service import OrchestratorService
from src.api.v1.dependencies import get_orchestrator_service
from src.core.telemetry.events import EVENT_BUS


# Request models
class SendMessageRequest(BaseModel):
    """Request model for sending a message"""
    agent_id: str = Field(..., description="Target agent identifier")
    message: str = Field(..., min_length=1, description="Message content")
    sender: Optional[str] = Field("user", description="Message sender (user or agent_key)")


class MessageResponse(BaseModel):
    """Response model for message information"""
    id: int = Field(..., description="Message sequence number")
    group_id: str = Field(..., description="Group identifier")
    sender: str = Field(..., description="Message sender")
    role: str = Field(..., description="Sender role (user/agent/system)")
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: float = Field(..., description="Creation timestamp")


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
    Send a message to a group - handles both user and agent messages uniformly.

    All messages go through the router for consistent mention processing.
    """
    try:
        message = request.message
        sender = request.sender or "user"

        # For user messages, add @mention if needed (preserves existing behavior)
        if sender == "user":
            # Check if this is a single-agent group
            group_agents = service.list_group_agents(group_id)

            if len(group_agents) == 1:
                # Single agent - no @mention needed
                pass
            else:
                # Multiple agents - add @mention if not present
                if not message.strip().startswith(f"@{request.agent_id}"):
                    message = f"@{request.agent_id} {message}"

        # For agent messages, pass through as-is (router will handle @mentions)
        print(f"🚀 Processing {sender} message for group {group_id}: {message[:100]}...")

        await service.process_message(group_id, message, sender)

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



@router.get("/groups/{group_id}/events")
async def stream_group_events(group_id: str):
    """
    Server-Sent Events stream for real-time group updates.

    Streams messages, user mentions, and other events as they happen.
    Frontend can listen to this for real-time updates and sound notifications.
    """
    async def event_generator():
        """Generate Server-Sent Events for the specified group"""

        # Send initial connection message
        yield f"data: {json.dumps({'type': 'connected', 'group_id': group_id, 'timestamp': asyncio.get_event_loop().time()})}\n\n"

        while True:
            try:
                # Drain events from the event bus
                events = await EVENT_BUS.drain(limit=50)

                for event in events:
                    # Only send events for this group
                    if event.group_id == group_id:
                        event_data = {
                            'type': event.kind,
                            'group_id': event.group_id,
                            'agent_key': event.agent_key,
                            'timestamp': event.ts,
                            'payload': event.payload
                        }

                        # Add sound notification flag for user mentions
                        if event.kind == 'user_mention':
                            event_data['sound_notification'] = True

                        yield f"data: {json.dumps(event_data)}\n\n"

                # Wait before next poll - reduced to 50ms for near-real-time updates
                await asyncio.sleep(0.05)

            except Exception as e:
                # Send error event
                error_data = {
                    'type': 'error',
                    'group_id': group_id,
                    'timestamp': asyncio.get_event_loop().time(),
                    'payload': {'error': str(e)}
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                await asyncio.sleep(5)  # Longer wait on error

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )


@router.post("/groups/{group_id}/stop")
async def stop_group_chain(
    group_id: str,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Stop agent chain for a specific group.

    This will prevent new agent responses from being processed,
    effectively stopping the agent conversation chain for this group only.
    """
    try:
        # Stop the group chain
        await service.stop_group_chain(group_id)

        return {
            "message": f"Agent chain stopped for group {group_id}",
            "group_id": group_id,
            "stopped": True
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop group chain: {str(e)}"
        )