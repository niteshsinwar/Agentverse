#!/usr/bin/env python3

"""
FastAPI REST API Server for Agentic SF Desktop
Wraps existing app/ functionality without modifying it
"""

from __future__ import annotations
import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

# Add the project root to Python path so we can import from app/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables from .env file (IMPORTANT!)
from dotenv import load_dotenv
load_dotenv()

from app.agents.orchestrator import AgentOrchestrator
from app.agents.router import Router
from app.memory import session_store
from app.document_processing.manager import document_manager
from app.telemetry.events import EVENT_BUS
from app.agents.registry import discover_agents
import json
import os
import shutil
import yaml
import ast
import importlib
import subprocess
import sys
from typing import List

# Pydantic models for API
class CreateGroupRequest(BaseModel):
    name: str

class AddAgentRequest(BaseModel):
    agent_key: str

class SendMessageRequest(BaseModel):
    agent_id: str
    message: str

class CreateAgentRequest(BaseModel):
    key: str
    name: str
    description: str
    emoji: str
    tools: List[str]
    mcpConfig: Dict[str, Any]
    toolsCode: str

class UpdateAgentRequest(BaseModel):
    name: str
    description: str
    emoji: str
    tools: List[str]
    mcpConfig: Dict[str, Any]
    toolsCode: str

class ValidateAgentRequest(BaseModel):
    toolsCode: str
    dependencies: List[str] = []

class GroupResponse(BaseModel):
    id: str
    name: str
    created_at: float
    updated_at: float

class AgentResponse(BaseModel):
    key: str
    name: str
    description: str
    emoji: str

class MessageResponse(BaseModel):
    id: int
    group_id: str
    sender: str
    role: str
    content: str
    metadata: Optional[Dict[str, Any]]
    created_at: float

class DocumentResponse(BaseModel):
    id: str
    filename: str
    size: int
    upload_time: float
    agent_id: str
    group_id: str

# Global orchestrator and router instances
orchestrator: Optional[AgentOrchestrator] = None
router: Optional[Router] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global orchestrator, router
    try:
        # Initialize orchestrator and router exactly like Gradio does
        print("🚀 API Server: Initializing orchestrator...")
        orchestrator = AgentOrchestrator()  # Agents are discovered in constructor
        router = Router(orchestrator)
        
        # Verify agents are loaded (same as Gradio's state.py)
        agents = orchestrator.list_available_agents()
        print(f"✅ API Server: Orchestrator and Router initialized successfully with {len(agents)} agents: {list(agents.keys())}")
        
        # Touch database and ensure initialization like Gradio does
        await asyncio.sleep(0.5)
        _ = session_store.list_groups()
        
        # Check if environment variables are set up correctly
        import os
        api_keys = {
            'OPENAI_API_KEY': '✅' if os.getenv('OPENAI_API_KEY') else '❌',
            'GEMINI_API_KEY': '✅' if os.getenv('GEMINI_API_KEY') else '❌', 
            'ANTHROPIC_API_KEY': '✅' if os.getenv('ANTHROPIC_API_KEY') else '❌',
            'GITHUB_TOKEN': '✅' if os.getenv('GITHUB_TOKEN') else '❌'
        }
        print(f"🔑 API Keys status: {api_keys}")
        
    except Exception as e:
        print(f"❌ API Server: Failed to initialize orchestrator: {e}")
        import traceback
        traceback.print_exc()
        raise
    yield
    # Shutdown
    orchestrator = None
    router = None

# Create FastAPI app
app = FastAPI(
    title="Agentic SF Desktop API",
    description="REST API for the Agentic Salesforce Developer Assistant",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for desktop app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "https://tauri.localhost"],  # Tauri app origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Groups endpoints
@app.get("/api/groups", response_model=List[GroupResponse])
async def get_groups():
    """Get all groups"""
    groups = session_store.list_groups()
    return [
        GroupResponse(
            id=group["id"],
            name=group["name"],
            created_at=group["created_at"],
            updated_at=group["updated_at"]
        )
        for group in groups
    ]

@app.post("/api/groups", response_model=GroupResponse)
async def create_group(request: CreateGroupRequest):
    """Create a new group"""
    group_id = session_store.create_group(request.name)
    groups = session_store.list_groups()
    group = next((g for g in groups if g["id"] == group_id), None)
    if not group:
        raise HTTPException(status_code=500, detail="Failed to create group")
    
    return GroupResponse(
        id=group["id"],
        name=group["name"],
        created_at=group["created_at"],
        updated_at=group["updated_at"]
    )

@app.delete("/api/groups/{group_id}")
async def delete_group(group_id: str):
    """Delete a group"""
    session_store.delete_group(group_id)
    return {"message": "Group deleted successfully"}

# Agents endpoints
@app.get("/api/agents/available", response_model=Dict[str, AgentResponse])
async def get_available_agents():
    """Get all available agents"""
    if not router or not orchestrator:
        raise HTTPException(status_code=500, detail="System not initialized")
    
    agents_specs = orchestrator.list_available_agents()
    return {
        key: AgentResponse(
            key=spec.key,
            name=spec.name,
            description=spec.description,
            emoji=spec.emoji
        )
        for key, spec in agents_specs.items()
    }

@app.get("/api/groups/{group_id}/agents", response_model=List[AgentResponse])
async def get_group_agents(group_id: str):
    """Get agents in a specific group"""
    if not router or not orchestrator:
        raise HTTPException(status_code=500, detail="System not initialized")
    
    agents_specs = orchestrator.list_available_agents()
    group_agent_keys = session_store.list_group_agents(group_id)
    
    return [
        AgentResponse(
            key=spec.key,
            name=spec.name,
            description=spec.description,
            emoji=spec.emoji
        )
        for key, spec in agents_specs.items()
        if key in group_agent_keys
    ]

@app.post("/api/groups/{group_id}/agents")
async def add_agent_to_group(group_id: str, request: AddAgentRequest):
    """Add an agent to a group"""
    session_store.add_agent_to_group(group_id, request.agent_key)
    return {"message": "Agent added to group successfully"}

@app.delete("/api/groups/{group_id}/agents/{agent_key}")
async def remove_agent_from_group(group_id: str, agent_key: str):
    """Remove an agent from a group"""
    session_store.remove_agent_from_group(group_id, agent_key)
    return {"message": "Agent removed from group successfully"}

# Messages endpoints
@app.get("/api/groups/{group_id}/messages", response_model=List[MessageResponse])
async def get_group_messages(group_id: str):
    """Get messages for a group"""
    messages = session_store.get_history(group_id)
    return [
        MessageResponse(
            id=i,  # Use index as ID since get_history doesn't return ID
            group_id=group_id,
            sender=msg["sender"],
            role=msg["role"],
            content=msg["content"],
            metadata=msg["metadata"],
            created_at=msg["created_at"]
        )
        for i, msg in enumerate(messages)
    ]

@app.post("/api/groups/{group_id}/messages")
async def send_message(group_id: str, request: SendMessageRequest):
    """Send a message to an agent - synchronous like Gradio's on_send"""
    if not router:
        raise HTTPException(status_code=500, detail="Router not initialized")
    
    try:
        # Format message with agent mention if not already present, just like Gradio does
        message = request.message
        if not message.strip().startswith(f"@{request.agent_id}"):
            message = f"@{request.agent_id} {message}"
        
        print(f"🚀 Processing message for group {group_id}: {message[:100]}...")
        
        # Use the same handler logic as Gradio's on_send function
        await router.handle_user_message(group_id, message)
        
        # Handle any mentions and triggers (same as Gradio)
        await check_for_mentions_and_trigger(group_id)
        
        print(f"✅ Message processed successfully for group {group_id}")
        return {"message": "Message sent successfully"}
        
    except Exception as e:
        error_msg = f"Error processing message: {str(e)}"
        print(f"❌ Message processing failed: {error_msg}")
        import traceback
        traceback.print_exc()
        
        # Store error message in session store like Gradio does
        session_store.append_message(
            group_id=group_id,
            sender="system",
            role="system",
            content=error_msg,
            metadata={"error_type": "message_processing", "original_message": request.message}
        )
        raise HTTPException(status_code=500, detail=error_msg)

async def check_for_mentions_and_trigger(group_id: str):
    """Check for agent mentions and trigger responses - copied from Gradio handlers"""
    if not router:
        return
        
    history = session_store.get_history(group_id)
    if not history:
        return
        
    last_msg = history[-1]
    if not last_msg or last_msg.get("role") != "agent":
        return
        
    content = last_msg.get("content", "").strip()
    if not content or "@" not in content:
        return
        
    parsed = router.parse(content)
    if not parsed:
        return
        
    agent_key, agent_content = parsed
    if agent_key.lower() == "user":
        return
        
    members = set(session_store.list_group_agents(group_id))
    if agent_key not in members:
        return
        
    agent = await router.o.get_agent(agent_key)
    reply = await agent.respond(agent_content, group_id=group_id, orchestrator=router.o)
    
    from app.telemetry.events import emit_message
    session_store.append_message(group_id, sender=agent_key, role="agent", content=str(reply), metadata={"agent_key": agent_key})
    await emit_message(group_id, sender=agent_key, role="agent", content=str(reply), agent_key=agent_key)
    
    # Recursively handle any further mentions
    await check_for_mentions_and_trigger(group_id)

# Documents endpoints
@app.get("/api/groups/{group_id}/documents")
async def get_group_documents(group_id: str):
    """Get documents for a group - matches Gradio's load_documents function"""
    if not group_id:
        return []
    try:
        # Use the same logic as Gradio's load_documents function
        documents = session_store.get_group_documents(group_id)
        result = []
        for doc in documents:
            md = doc.get('metadata', {})
            filename = md.get('filename', 'Unknown')
            sender = doc.get('sender', 'Unknown')
            target = md.get('target_agent', 'Unknown')
            size = md.get('file_size', 0)
            
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
                
            import datetime
            date_str = datetime.datetime.fromtimestamp(doc.get('created_at', 0)).strftime("%Y-%m-%d %H:%M")
            
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
                "original_prompt": md.get('original_prompt', ''),
                "content_summary": md.get('content_summary', ''),
                "extracted_content": md.get('extracted_content', '')
            })
        return result
    except Exception as e:
        print(f"❌ Error loading documents: {e}")
        return []

@app.post("/api/groups/{group_id}/documents/upload")
async def upload_document(
    group_id: str,
    file: UploadFile = File(...),
    agent_id: str = Form(...),
    message: str = Form(default="")
):
    """Upload a document for an agent in a group - matches Gradio's document processing"""
    try:
        # Create temporary file path like Gradio's UploadFile
        import tempfile
        temp_file_path = None
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            # Use the same document processing as Gradio's on_send function
            result = document_manager.process_and_store_document(
                uploaded_file=temp_file_path,  # Pass file path like Gradio
                group_id=group_id,
                agent_id=agent_id,
                sender_type="user"
            )
            
            if result['success']:
                # Store document message in session like Gradio does
                session_store.append_document_message(
                    group_id=group_id,
                    sender="user",
                    filename=file.filename,
                    document_id=result['document_id'],
                    target_agent=agent_id,
                    file_size=len(content),
                    file_extension=Path(file.filename).suffix if file.filename else "",
                    original_prompt=message,
                    extracted_content=result.get('extracted_content', ''),
                    content_summary=result.get('content_summary', '')
                )
                
                # Store enhanced system message with user prompt, agent mention, and AI analysis
                summary_text = result.get('content_summary') or result.get('extracted_content') or ''
                if summary_text:
                    # Create comprehensive system message as per user requirements
                    system_message_content = (
                        f"📄 **Document uploaded**: {file.filename}\n"
                        f"**Target Agent**: @{agent_id}\n"
                        f"**User Prompt**: {message if message else 'Please analyze this document'}\n"
                        f"**AI Analysis Summary**: {summary_text[:500]}{'...' if len(summary_text) > 500 else ''}\n\n"
                        f"🤖 Document processed and routed to @{agent_id} for analysis."
                    )
                    
                    session_store.append_message(
                        group_id, sender="system", role="system",
                        content=system_message_content,
                        metadata={
                            "message_type": "document_processed",
                            "document_id": result['document_id'],
                            "target_agent": agent_id,
                            "user_prompt": message,
                            "summary": summary_text,
                            "filename": file.filename
                        }
                    )
                    
                    # Now route to the agent for response (as per your requirement)
                    try:
                        agent_prompt = f"Document Analysis Request:\n\n**Document**: {file.filename}\n**User Request**: {message if message else 'Please analyze this document'}\n\n**Document Summary**: {summary_text}\n\nPlease provide your analysis and response based on the document content and user request."
                        
                        agent_response = await orchestrator.process_user_message(group_id, agent_id, agent_prompt)
                        
                        # Store agent response
                        session_store.append_message(
                            group_id=group_id,
                            sender=agent_id,
                            role="agent",
                            content=agent_response,
                            metadata={"agent_key": agent_id, "responding_to": "document_upload"}
                        )
                        
                    except Exception as e:
                        print(f"⚠️ Failed to get agent response for document: {e}")
                        # Store error message if agent fails
                        session_store.append_message(
                            group_id=group_id,
                            sender="system",
                            role="system",
                            content=f"⚠️ {agent_id} could not analyze the document at this time. Please try again or mention the agent directly.",
                            metadata={"error": str(e), "agent_id": agent_id}
                        )
                
                return {
                    "success": True,
                    "document_id": result['document_id'],
                    "filename": file.filename,
                    "size": len(content),
                    "agent_id": agent_id,
                    "group_id": group_id,
                    "message": "Document uploaded and processed successfully",
                    "content_summary": result.get('content_summary', ''),
                    "extracted_content": result.get('extracted_content', '')
                }
            else:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to process document: {result.get('error', 'Unknown error')}"
                )
                
        finally:
            # Clean up temporary file
            if temp_file_path and Path(temp_file_path).exists():
                Path(temp_file_path).unlink()
                
    except Exception as e:
        error_msg = f"Failed to upload document: {str(e)}"
        print(f"❌ Document upload error: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

# Events endpoint (Server-Sent Events)
@app.get("/api/groups/{group_id}/events")
async def stream_events(group_id: str):
    """Stream real-time events for a group"""
    async def event_generator():
        # Subscribe to events for this group
        event_queue = asyncio.Queue()
        
        def event_handler(event_type: str, data: Dict[str, Any]):
            if data.get("group_id") == group_id:
                try:
                    event_queue.put_nowait({
                        "type": event_type,
                        "data": data,
                        "timestamp": data.get("timestamp", 0)
                    })
                except Exception:
                    pass  # Queue full, skip event
        
        # Register event handler
        EVENT_BUS.subscribe("*", event_handler)
        
        try:
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connection', 'data': {'status': 'connected', 'group_id': group_id}, 'timestamp': asyncio.get_event_loop().time()})}\n\n"
            
            # Stream events
            while True:
                try:
                    event = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield f"data: {json.dumps({'type': 'heartbeat', 'data': {}, 'timestamp': asyncio.get_event_loop().time()})}\n\n"
        finally:
            # Unregister event handler
            EVENT_BUS.unsubscribe("*", event_handler)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

# =================== AGENT MANAGEMENT ENDPOINTS ===================

@app.get("/api/agents")
async def list_agents():
    """Get list of all available agents"""
    try:
        agents = discover_agents()
        agent_list = []
        
        for key, spec in agents.items():
            agent_list.append({
                "key": spec.key,
                "name": spec.name,
                "description": spec.description,
                "emoji": spec.emoji,
                "tools": getattr(spec, 'tools', []),
                "mcpConfig": getattr(spec, 'mcp_config', {}),
                "toolsCode": ""  # Will be loaded from tools.py if needed
            })
        
        return agent_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")

@app.post("/api/agents/create")
async def create_agent(request: CreateAgentRequest):
    """Create a new agent with all required files"""
    try:
        agent_dir = Path(f"app/agents/{request.key}")
        
        # Check if agent already exists
        if agent_dir.exists():
            raise HTTPException(status_code=400, detail=f"Agent {request.key} already exists")
        
        # Create agent directory
        agent_dir.mkdir(parents=True, exist_ok=True)
        
        # Create agent.yaml following template structure
        agent_config = {
            "name": request.name,
            "description": request.description,
            "emoji": request.emoji,
            "document_access": {
                "enabled": True,
                "supported_formats": ["txt", "csv", "json", "pdf", "docx", "md"],
                "max_file_size_mb": 10,
                "ai_extraction": {
                    "enabled": True,
                    "generate_summary": True
                }
            },
            "behavior": {
                "max_iterations": 5,
                "temperature": 0.2,
                "model_override": None
            }
        }
        
        with open(agent_dir / "agent.yaml", "w") as f:
            yaml.dump(agent_config, f, default_flow_style=False)
        
        # Create tools.py following template structure
        default_tools_content = f'''"""
Custom tools for {request.name}
All functions decorated with @agent_tool will be auto-discovered
"""
from app.agents.base_agent import agent_tool
from typing import Dict, Any, List, Optional

@agent_tool
def example_tool(input_text: str, option: str = "default") -> Dict[str, Any]:
    """
    Example tool that demonstrates the standard pattern
    Args:
        input_text: The text to process
        option: Processing option with default value
    Returns:
        Dictionary with processed results
    """
    # Your tool implementation here
    result = f"Processed '{{input_text}}' with option '{{option}}'"
    
    return {{
        "success": True,
        "result": result,
        "input": input_text,
        "option_used": option
    }}

# Add your custom tools here following the same pattern:
# 1. Decorate with @agent_tool
# 2. Add type hints for parameters and return value  
# 3. Include clear docstring with Args and Returns
# 4. Handle edge cases gracefully

{request.toolsCode if request.toolsCode else ""}
'''
        
        tools_content = default_tools_content
        
        with open(agent_dir / "tools.py", "w") as f:
            f.write(tools_content)
        
        # Create __init__.py
        init_content = "# Agent module init\\n"
        
        with open(agent_dir / "__init__.py", "w") as f:
            f.write(init_content)
        
        # Create mcp.json if MCP config provided
        if request.mcpConfig:
            with open(agent_dir / "mcp.json", "w") as f:
                json.dump(request.mcpConfig, f, indent=2)
        
        # Refresh orchestrator to pick up new agent
        global orchestrator
        orchestrator.refresh_agents()
        
        return {
            "success": True,
            "message": f"Agent {request.key} created successfully",
            "agent": {
                "key": request.key,
                "name": request.name,
                "description": request.description,
                "emoji": request.emoji,
                "tools": request.tools,
                "mcpConfig": request.mcpConfig
            }
        }
        
    except Exception as e:
        print(f"❌ Error creating agent {request.key}: {str(e)}")
        import traceback
        traceback.print_exc()
        # Clean up on failure
        if agent_dir.exists():
            shutil.rmtree(agent_dir)
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")

@app.get("/api/agents/{agent_key}")
async def get_agent(agent_key: str):
    """Get details of a specific agent"""
    try:
        agents = discover_agents()
        
        if agent_key not in agents:
            raise HTTPException(status_code=404, detail=f"Agent {agent_key} not found")
        
        spec = agents[agent_key]
        agent_dir = Path(f"app/agents/{agent_key}")
        
        # Read tools.py content if it exists
        tools_code = ""
        tools_file = agent_dir / "tools.py"
        if tools_file.exists():
            with open(tools_file, "r") as f:
                tools_code = f.read()
        
        return {
            "key": spec.key,
            "name": spec.name,
            "description": spec.description,
            "emoji": spec.emoji,
            "tools": getattr(spec, 'tools', []),
            "mcpConfig": getattr(spec, 'mcp_config', {}),
            "toolsCode": tools_code
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent: {str(e)}")

@app.put("/api/agents/{agent_key}")
async def update_agent(agent_key: str, request: UpdateAgentRequest):
    """Update an existing agent"""
    try:
        agent_dir = Path(f"app/agents/{agent_key}")
        
        if not agent_dir.exists():
            raise HTTPException(status_code=404, detail=f"Agent {agent_key} not found")
        
        # Update agent.yaml following template structure
        agent_config = {
            "name": request.name,
            "description": request.description,
            "emoji": request.emoji,
            "document_access": {
                "enabled": True,
                "supported_formats": ["txt", "csv", "json", "pdf", "docx", "md"],
                "max_file_size_mb": 10,
                "ai_extraction": {
                    "enabled": True,
                    "generate_summary": True
                }
            },
            "behavior": {
                "max_iterations": 5,
                "temperature": 0.2,
                "model_override": None
            }
        }
        
        with open(agent_dir / "agent.yaml", "w") as f:
            yaml.dump(agent_config, f, default_flow_style=False)
        
        # Update tools.py
        if request.toolsCode:
            with open(agent_dir / "tools.py", "w") as f:
                f.write(request.toolsCode)
        
        # Update mcp.json
        if request.mcpConfig:
            with open(agent_dir / "mcp.json", "w") as f:
                json.dump(request.mcpConfig, f, indent=2)
        
        # Reload orchestrator to pick up changes
        global orchestrator
        orchestrator = AgentOrchestrator()
        
        return {
            "success": True,
            "message": f"Agent {agent_key} updated successfully",
            "agent": {
                "key": agent_key,
                "name": request.name,
                "description": request.description,
                "emoji": request.emoji,
                "tools": request.tools,
                "mcpConfig": request.mcpConfig
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update agent: {str(e)}")

@app.delete("/api/agents/{agent_key}")
async def delete_agent(agent_key: str):
    """Delete an agent and all its files"""
    try:
        agent_dir = Path(f"app/agents/{agent_key}")
        
        if not agent_dir.exists():
            raise HTTPException(status_code=404, detail=f"Agent {agent_key} not found")
        
        # Remove agent directory and all contents
        shutil.rmtree(agent_dir)
        
        # Refresh orchestrator to remove agent
        global orchestrator
        orchestrator.refresh_agents()
        
        return {
            "success": True,
            "message": f"Agent {agent_key} deleted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")

@app.get("/api/agents/{agent_key}/tools")
async def get_agent_tools_code(agent_key: str):
    """Get the tools.py code for an agent"""
    try:
        agent_dir = Path(f"app/agents/{agent_key}")
        tools_file = agent_dir / "tools.py"
        
        if not tools_file.exists():
            raise HTTPException(status_code=404, detail=f"Tools file not found for agent {agent_key}")
        
        with open(tools_file, "r") as f:
            tools_code = f.read()
        
        return {
            "agent_key": agent_key,
            "tools_code": tools_code
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tools code: {str(e)}")

@app.put("/api/agents/{agent_key}/tools")
async def update_agent_tools_code(agent_key: str, tools_code: str = Form(...)):
    """Update the tools.py code for an agent"""
    try:
        agent_dir = Path(f"app/agents/{agent_key}")
        
        if not agent_dir.exists():
            raise HTTPException(status_code=404, detail=f"Agent {agent_key} not found")
        
        # Write updated tools code
        with open(agent_dir / "tools.py", "w") as f:
            f.write(tools_code)
        
        # Reload orchestrator to pick up changes
        global orchestrator
        orchestrator = AgentOrchestrator()
        
        return {
            "success": True,
            "message": f"Tools code updated for agent {agent_key}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update tools code: {str(e)}")

@app.get("/api/system/modules")
async def get_available_modules():
    """Get list of available Python modules"""
    try:
        # Get commonly used modules and check if they're available
        common_modules = [
            'requests', 'numpy', 'pandas', 'matplotlib', 'seaborn', 'plotly',
            'scikit-learn', 'tensorflow', 'torch', 'opencv-cv2', 'pillow',
            'beautifulsoup4', 'selenium', 'scrapy', 'flask', 'fastapi',
            'sqlalchemy', 'psycopg2', 'pymongo', 'redis', 'celery',
            'asyncio', 'aiohttp', 'websockets', 'pydantic', 'click',
            'typer', 'rich', 'tabulate', 'tqdm', 'python-dotenv',
            'pyyaml', 'toml', 'jsonschema', 'dateutil', 'pytz'
        ]
        
        available_modules = []
        for module in common_modules:
            try:
                importlib.import_module(module)
                available_modules.append({
                    "name": module,
                    "status": "available",
                    "version": None  # Could add version detection later
                })
            except ImportError:
                available_modules.append({
                    "name": module,
                    "status": "not_installed"
                })
        
        # Also get system Python info
        python_info = {
            "version": sys.version,
            "executable": sys.executable,
            "path": sys.path[:3]  # First 3 paths only
        }
        
        return {
            "python_info": python_info,
            "modules": available_modules,
            "total_checked": len(common_modules)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system info: {str(e)}")

@app.post("/api/agents/validate")
async def validate_agent_code(request: ValidateAgentRequest):
    """Validate agent tools code before creation"""
    try:
        validation_result = {
            "syntax_valid": False,
            "functions_found": [],
            "imports_found": [],
            "missing_dependencies": [],
            "errors": [],
            "warnings": []
        }
        
        # 1. Check Python syntax
        try:
            ast.parse(request.toolsCode)
            validation_result["syntax_valid"] = True
        except SyntaxError as e:
            validation_result["errors"].append(f"Syntax Error: {str(e)}")
            return validation_result
        
        # 2. Extract functions and imports
        try:
            tree = ast.parse(request.toolsCode)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    validation_result["functions_found"].append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        validation_result["imports_found"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        validation_result["imports_found"].append(node.module)
        
        except Exception as e:
            validation_result["warnings"].append(f"Code analysis warning: {str(e)}")
        
        # 3. Check for missing dependencies
        for module in validation_result["imports_found"]:
            if module not in ['typing', 'os', 'sys', 'json', 're', 'datetime', 'pathlib']:  # Built-in modules
                try:
                    importlib.import_module(module.split('.')[0])  # Check root module
                except ImportError:
                    validation_result["missing_dependencies"].append(module)
        
        # 4. Check for @agent_tool decorators
        agent_tool_functions = []
        lines = request.toolsCode.split('\n')
        for i, line in enumerate(lines):
            if '@agent_tool' in line and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.startswith('def '):
                    func_name = next_line.split('(')[0].replace('def ', '')
                    agent_tool_functions.append(func_name)
        
        if not agent_tool_functions:
            validation_result["warnings"].append("No @agent_tool decorated functions found. Tools may not be auto-discovered.")
        
        validation_result["agent_tool_functions"] = agent_tool_functions
        
        # 5. Validation summary
        is_valid = (
            validation_result["syntax_valid"] and
            len(validation_result["missing_dependencies"]) == 0 and
            len(validation_result["errors"]) == 0
        )
        
        validation_result["is_valid"] = is_valid
        validation_result["summary"] = f"Found {len(agent_tool_functions)} agent tools, {len(validation_result['missing_dependencies'])} missing dependencies"
        
        return validation_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.post("/api/agents/test-register")
async def test_agent_registration(request: CreateAgentRequest):
    """Test agent registration without creating files (dry run)"""
    try:
        # Validate the agent configuration
        validation_errors = []
        
        # Check agent key format
        if not request.key.replace('_', '').isalnum():
            validation_errors.append("Agent key must contain only letters, numbers, and underscores")
        
        # Check if agent already exists
        if Path(f"app/agents/{request.key}").exists():
            validation_errors.append(f"Agent {request.key} already exists")
        
        # Validate tools code
        code_validation = await validate_agent_code(ValidateAgentRequest(
            toolsCode=request.toolsCode or "",
            dependencies=request.tools
        ))
        
        # Check MCP configuration
        mcp_errors = []
        try:
            if request.mcpConfig:
                # Basic validation of MCP structure
                if "mcpServers" not in request.mcpConfig:
                    mcp_errors.append("MCP config missing 'mcpServers' section")
                else:
                    for server_name, config in request.mcpConfig["mcpServers"].items():
                        if "command" not in config:
                            mcp_errors.append(f"MCP server '{server_name}' missing 'command'")
        except Exception as e:
            mcp_errors.append(f"Invalid MCP configuration: {str(e)}")
        
        # Test if agent would be discoverable
        discovery_test = {
            "agent_key_valid": len(validation_errors) == 0,
            "code_valid": code_validation.get("is_valid", False),
            "mcp_valid": len(mcp_errors) == 0,
            "would_register": False
        }
        
        discovery_test["would_register"] = (
            discovery_test["agent_key_valid"] and 
            discovery_test["code_valid"] and 
            discovery_test["mcp_valid"]
        )
        
        return {
            "success": True,
            "test_results": {
                "validation_errors": validation_errors,
                "code_validation": code_validation,
                "mcp_errors": mcp_errors,
                "discovery_test": discovery_test,
                "ready_to_create": discovery_test["would_register"]
            },
            "agent_preview": {
                "key": request.key,
                "name": request.name,
                "description": request.description,
                "emoji": request.emoji,
                "tools_count": len(code_validation.get("agent_tool_functions", [])),
                "dependencies_count": len(code_validation.get("missing_dependencies", []))
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test registration failed: {str(e)}")

# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "orchestrator_ready": orchestrator is not None,
        "router_ready": router is not None,
        "timestamp": asyncio.get_event_loop().time()
    }

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        access_log=True
    )