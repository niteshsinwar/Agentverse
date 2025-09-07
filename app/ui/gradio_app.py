# =========================================
# File: app/ui/gradio_app.py
# Purpose: WhatsApp‑style UI with transparency panel for tool/MCP/agent calls
# =========================================
from __future__ import annotations
import gradio as gr
from typing import List, Dict, Any, Tuple
import asyncio
import time

from app.agents.orchestrator import AgentOrchestrator
from app.agents.registry import discover_agents
from app.agents.router import Router
from app.memory import session_store
from app.telemetry.events import emit_message

# Global initialization state
_initialization_complete = False
_initialization_lock = asyncio.Lock()

async def ensure_initialization():
    """Ensure all components are properly initialized before UI interactions."""
    global _initialization_complete
    
    if _initialization_complete:
        return True
    
    async with _initialization_lock:
        if _initialization_complete:
            return True
        
        try:
            # Give time for database connections to stabilize
            await asyncio.sleep(0.5)
            
            # Test database connection
            groups = session_store.list_groups()
            
            # Test agent discovery
            agents = discover_agents()
            
            # Mark as complete
            _initialization_complete = True
            print("✅ Initialization complete - UI ready for interactions")
            return True
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False


def get_recent_interactions(group_id):
    """Get recent agent interactions for the interactions panel."""
    if not group_id:
        return ""
    
    try:
        # Get raw history directly from session store, not the formatted chat pairs
        history = session_store.get_history(group_id)
    except Exception as e:
        return f"Error loading history: {str(e)}"
    
    interactions = []
    
    for msg in history[-10:]:  # Last 10 messages
        # Add safety check for msg type
        if not isinstance(msg, dict):
            continue
            
        role = msg.get("role", "")
        sender = msg.get("sender", "")
        content = msg.get("content", "")
        
        if role == "system" and "transferred control" in content:
            interactions.append(f"🔄 {content}")
        elif role == "agent":
            agent_key = msg.get("metadata", {}).get("agent_key", sender)
            # Truncate long messages
            short_content = content[:50] + "..." if len(content) > 50 else content
            interactions.append(f"🤖 {agent_key}: {short_content}")
        elif role == "user":
            short_content = content[:50] + "..." if len(content) > 50 else content
            interactions.append(f"👤 User: {short_content}")
    
    return "\n".join(interactions) if interactions else "No interactions yet..."


from app.memory import session_store
from app.telemetry.events import EVENT_BUS


# ---------- Helpers to render history into Chatbot format ----------

def to_chat_pairs(history: List[Dict[str, Any]]) -> List[List[str]]:
    pairs: List[List[str]] = []
    
    # Get all events for this timeline (tool calls, MCP calls, etc.)
    try:
        # Get recent events from the event bus
        import asyncio
        if hasattr(asyncio, '_get_running_loop') and asyncio._get_running_loop() is not None:
            # We're in an async context, but this function is sync
            # For now, just render messages without events
            events = []
        else:
            events = []
    except:
        events = []
    
    # Render messages and intersperse tool events
    for rec in history:
        if rec["role"] == "user":
            user_msg = f"**You:** {rec['content']}"
            pairs.append([user_msg, None])
        elif rec["role"] == "agent":
            # Get agent name if available
            sender = rec.get("sender", "Agent")
            agent_msg = f"**{sender}:** {rec['content']}"
            pairs.append([None, agent_msg])
        elif rec["role"] == "tool_call":
            # Show tool calls - content is already formatted
            pairs.append([None, rec['content']])
        elif rec["role"] == "tool_result":
            # Show tool results - content is already formatted
            pairs.append([None, rec['content']])
        elif rec["role"] == "tool_error":
            # Show tool errors - content is already formatted
            pairs.append([None, rec['content']])
        elif rec["role"] == "mcp_call":
            # Show MCP calls inline (same as tool calls)
            server = rec.get('server', 'unknown')
            tool_name = rec.get('tool_name', 'unknown')
            params = rec.get('params', {})
            status = rec.get('status', 'running')
            
            if status == "start":
                mcp_msg = f"🔧 **MCP Call:** `{server}/{tool_name}({', '.join(f'{k}={v}' for k, v in params.items())})`"
            elif status == "end":
                mcp_msg = f"✅ **MCP Completed:** `{server}/{tool_name}`"
            else:
                mcp_msg = f"⚠️ **MCP {status.title()}:** `{server}/{tool_name}`"
                
            pairs.append([None, mcp_msg])
        elif rec["role"] == "tool_error":
            # Show tool errors
            pairs.append([None, rec['content']])
        elif rec["role"] == "mcp_result":
            # Show MCP results
            pairs.append([None, rec['content']])
        elif rec["role"] in ["system", "tool_start", "tool_end", "mcp_start", "mcp_end"]:
            # Skip duplicate tool event messages - we already show them via tool_call/tool_result
            continue
        else:
            # Other roles show as agent side but without system prefix if it's tool-related
            if "tool" in rec["role"].lower() or "mcp" in rec["role"].lower():
                # Skip tool-related messages that aren't in our main categories
                continue
            pairs.append([None, f"**[{rec['role']}]:** {rec['content']}"])
    return pairs


# ---------- Build App ----------

o = AgentOrchestrator()
router = Router(o)
agent_catalog = discover_agents()  # key -> AgentSpec


CSS = """
/* WhatsApp-like bubbles */
.gr-chatbot {height: 100%;}
.bubble-user   {background: #d9fdd3; color: #111; border-radius: 8px 8px 0 8px; padding: 8px 10px;}
.bubble-agent  {background: #fff;    color: #111; border-radius: 8px 8px 8px 0; padding: 8px 10px; border: 1px solid #eee;}
.sidebar       {background:#f9fafb; border-left: 1px solid #e5e7eb;}
.event-item    {font-size: 13px; border-bottom: 1px dashed #e5e7eb; padding: 6px 0;}
.event-kind    {font-weight: 600; margin-right: 6px;}
.event-meta    {opacity: .8;}
.header        {display:flex; align-items:center; justify-content:space-between;}
.badge         {background:#eef2ff; color:#3730a3; padding:2px 8px; border-radius: 999px; font-size:12px;}
.table td, .table th { border-bottom: 1px solid #eee; padding: 6px 8px; }
"""


def ui_list_groups():
    return [(g["name"], g["id"]) for g in session_store.list_groups()]


def ui_list_agents():
    return [(f"@{k} — {spec.name}", k) for k, spec in agent_catalog.items()]


def ui_group_members(group_id: str) -> List[Tuple[str, str, str]]:
    if not group_id:
        return []
    keys = session_store.list_group_agents(group_id)
    out = []
    for k in keys:
        spec = agent_catalog.get(k)
        if spec:
            out.append((k, spec.name, spec.description))
        else:
            out.append((k, k, ""))
    return out


def render_events(evts: List[Dict[str, Any]]) -> str:
    # Render as HTML list
    parts = []
    for e in evts[-200:]:
        k = e["kind"]
        p = e["payload"]
        if k == "message":
            who = p.get("sender")
            parts.append(f"<div class='event-item'><span class='event-kind'>msg</span><span class='event-meta'> {who}</span>: {p.get('content')}</div>")
        elif k == "tool_call":
            parts.append(f"<div class='event-item'><span class='event-kind'>tool</span> {p.get('tool')} <span class='event-meta'>[{p.get('status')}]</span></div>")
        elif k == "tool_result":
            ex = p.get('excerpt', '')
            parts.append(f"<div class='event-item'><span class='event-kind'>tool✓</span> {p.get('tool')} → <span class='event-meta'>{ex}</span></div>")
        elif k == "mcp_call":
            parts.append(f"<div class='event-item'><span class='event-kind'>mcp</span> {p.get('server')}/{p.get('tool')} <span class='event-meta'>[{p.get('status')}]</span></div>")
        elif k == "agent_call":
            parts.append(f"<div class='event-item'><span class='event-kind'>agent</span> @{p.get('caller')} ➜ @{p.get('callee')} <span class='event-meta'>[{p.get('status')}]</span></div>")
        else:
            parts.append(f"<div class='event-item'><span class='event-kind'>{k}</span> {p}</div>")
    return "\n".join(parts) or "<div class='event-item'>No activity yet.</div>"


# --------- Gradio callbacks ---------

def on_create_group(name: str):
    gid = session_store.create_group(name or "New Group")
    choices = ui_list_groups()
    return gr.Dropdown(choices=choices, value=gid)


def on_refresh_groups():
    """Refresh the groups dropdown with latest data from database"""
    try:
        if not _initialization_complete:
            choices = [("⏳ Initializing...", "")]
        else:
            choices = ui_list_groups()
        current_value = choices[0][1] if choices else None
        return gr.Dropdown(choices=choices, value=current_value)
    except Exception as e:
        print(f"Error refreshing groups: {e}")
        return gr.Dropdown(choices=[("❌ Error", "")], value="")


def on_rename_group(gid: str, new_name: str):
    if gid:
        session_store.rename_group(gid, new_name)
    choices = ui_list_groups()
    return gr.Dropdown(choices=choices, value=gid)


def on_delete_group(gid: str):
    if gid:
        session_store.delete_group(gid)
    choices = ui_list_groups()
    return gr.Dropdown(choices=choices, value=None), [], [], ""


def on_add_agent(gid: str, agent_key: str):
    if gid and agent_key:
        session_store.add_agent_to_group(gid, agent_key)
    rows = [[k, n, d] for (k, n, d) in ui_group_members(gid)]
    return rows


def on_remove_agent(gid: str, agent_key: str):
    if gid and agent_key:
        session_store.remove_agent_from_group(gid, agent_key)
    rows = [[k, n, d] for (k, n, d) in ui_group_members(gid)]
    return rows


def ui_list_groups():
    """Get groups list with initialization check."""
    try:
        if not _initialization_complete:
            return [("⏳ Initializing...", "")]
        return [(g["name"], g["id"]) for g in session_store.list_groups()]
    except Exception as e:
        return [("❌ Error loading groups", "")]


def ui_list_agents():
    """Get agents list with initialization check."""
    try:
        if not _initialization_complete:
            return [("⏳ Loading agents...", "")]
        return [(f"@{k} — {spec.name}", k) for k, spec in agent_catalog.items()]
    except Exception as e:
        return [("❌ Error loading agents", "")]


def load_history(gid: str):
    """Load chat history with error handling."""
    try:
        if not _initialization_complete:
            return [["⏳ Loading...", None]]
        if not gid:
            return []
        hist = session_store.get_history(gid)
        return to_chat_pairs(hist)
    except Exception as e:
        print(f"Error loading history: {e}")
        return [["❌ Error loading messages", None]]


def get_recent_interactions(group_id: str) -> str:
    """Get recent agent interactions from the conversation history."""
    if not group_id:
        return ""
    
    try:
        # Get raw history directly from session store, not the formatted chat pairs
        history = session_store.get_history(group_id)
    except Exception as e:
        return f"Error loading history: {str(e)}"
    
    interactions = []
    
    for msg in history[-10:]:  # Last 10 messages
        # Add safety check for msg type
        if not isinstance(msg, dict):
            continue
            
        role = msg.get("role", "")
        sender = msg.get("sender", "")
        content = msg.get("content", "")
        
        if role == "system" and "transferred control" in content:
            interactions.append(f"🔄 {content}")
        elif role == "agent":
            agent_key = msg.get("metadata", {}).get("agent_key", sender)
            # Truncate long messages
            short_content = content[:50] + "..." if len(content) > 50 else content
            interactions.append(f"🤖 {agent_key}: {short_content}")
        elif role == "user":
            short_content = content[:50] + "..." if len(content) > 50 else content
            interactions.append(f"👤 User: {short_content}")
    
    return "\n".join(interactions) if interactions else "No interactions yet..."


async def on_send(gid: str, text: str):
    # Ensure initialization before processing
    if not await ensure_initialization():
        return load_history(""), "⏳ System initializing, please wait..."
    
    if not gid:
        return load_history(""), "Please select a group first"
    if not text.strip():
        return load_history(gid), ""
    
    try:
        # Process the initial message (from user)
        reply = await router.handle_user_message(gid, text)
        
        # After any agent responds, check if their response contains @mentions
        await check_for_mentions_and_trigger(gid)
        
        return load_history(gid), ""
    except Exception as e:
        print(f"Error sending message: {e}")
        return load_history(gid), text


async def check_for_mentions_and_trigger(gid: str):
    """Check the latest agent response for @mentions and trigger those agents."""
    try:
        history = session_store.get_history(gid)
        if not history:
            return
        
        # Check the last message
        last_msg = history[-1] if history else None
        if not last_msg or last_msg.get("role") != "agent":
            return
        
        content = last_msg.get("content", "").strip()
        if not content or "@" not in content:
            return
        
        print(f"DEBUG: Agent message content: '{content}'")
        
        # Parse @mention using router's method - check entire content for @mentions
        parsed = router.parse(content)
        print(f"DEBUG: Router parsed result: {parsed}")
        if not parsed:
            return
        
        agent_key, agent_content = parsed
        print(f"DEBUG: Found @mention for {agent_key}: {agent_content}")
        
        # Handle @user mentions - these don't trigger agents, just transfer control back to user
        if agent_key.lower() == "user":
            print("DEBUG: @user mentioned - transferring control back to user")
            return
        
        # Check if target agent exists in group
        members = set(session_store.list_group_agents(gid))
        if agent_key not in members:
            print(f"DEBUG: Agent {agent_key} not in group")
            return
        
        # Trigger the mentioned agent
        agent = router.o.get_agent(agent_key)
        reply = await agent.respond(agent_content, group_id=gid, orchestrator=router.o)
        
        # Save the response
        from app.telemetry.events import emit_message
        session_store.append_message(gid, sender=agent_key, role="agent", content=str(reply), metadata={"agent_key": agent_key})
        await emit_message(gid, sender=agent_key, role="agent", content=str(reply), agent_key=agent_key)
        
        # Recursively check if this agent also mentioned someone
        await check_for_mentions_and_trigger(gid)
        
    except Exception as e:
        print(f"Error checking mentions: {e}")


async def process_agent_messages(gid: str):
    """Process any new agent messages that contain @mentions."""
    try:
        # Get recent history to check for new agent messages
        history = session_store.get_history(gid)
        if not history:
            return
        
        # Check the last message for agent-posted messages with @mentions
        last_msg = history[-1] if history else None
        if (last_msg and 
            last_msg.get("role") == "agent" and 
            last_msg.get("content", "").startswith("@")):
            
            # Get the message content
            content = last_msg.get("content", "").strip()
            print(f"DEBUG: Processing agent message: {content}")
            
            # Parse the @mention like the router does
            parsed = router.parse(content)
            if parsed:
                target_agent_key, message_content = parsed
                print(f"DEBUG: Routing to target agent: {target_agent_key}")
                
                # Check if target agent exists in the group
                members = set(session_store.list_group_agents(gid))
                if target_agent_key not in members:
                    print(f"DEBUG: Target agent {target_agent_key} not in group")
                    return
                
                # Get the target agent and make it respond (same as router does)
                target_agent = router.o.get_agent(target_agent_key)
                reply = await target_agent.respond(message_content, group_id=gid, orchestrator=router.o)
                
                # Save the target agent's response
                from app.telemetry.events import emit_message
                session_store.append_message(gid, sender=target_agent_key, role="agent", content=str(reply), metadata={"agent_key": target_agent_key})
                await emit_message(gid, sender=target_agent_key, role="agent", content=str(reply), agent_key=target_agent_key)
                
                print(f"DEBUG: Target agent {target_agent_key} replied: {reply}")
                
                # Recursively check for more messages (in case the target agent also posts)
                await process_agent_messages(gid)
            
    except Exception as e:
        print(f"Error processing agent messages: {e}")


# Background task: poll EventBus and filter by group
async def poll_events(group_id: str) -> List[Dict[str, Any]]:
    evs = await EVENT_BUS.drain()
    # Keep a static buffer per session in State (we'll manage in UI)
    return [e.to_dict() for e in evs if e.group_id == group_id]


# ---------- Build UI ----------

def build_app() -> gr.Blocks:
    with gr.Blocks(css=CSS, fill_height=True) as demo:
        gr.Markdown("## Multi‑Agent Group Chat")
        with gr.Row():
            with gr.Column(scale=3):
                # Initialize groups dropdown (will be populated on page load)
                with gr.Row():
                    grp = gr.Dropdown(label="Group", choices=[], scale=4)
                    refresh_btn = gr.Button("🔄", scale=1, size="sm")
                with gr.Row():
                    new_name = gr.Textbox(label="Name", placeholder="New Group")
                    gr.Button("Create").click(on_create_group, inputs=[new_name], outputs=[grp])
                
                # Connect refresh button
                refresh_btn.click(on_refresh_groups, outputs=[grp])
                
                gr.Markdown("### Members (visible roster to all agents)")
                # Initialize with empty members (will be populated when group is selected)
                members = gr.Dataframe(
                    headers=["Agent Key", "Name", "Description"], 
                    value=[], 
                    interactive=False, 
                    wrap=True, 
                    row_count=(0, "dynamic")
                )
                
                with gr.Row():
                    rename_to = gr.Textbox(label="Rename to")
                    gr.Button("Rename").click(on_rename_group, inputs=[grp, rename_to], outputs=[grp])
                    delete_btn = gr.Button("Delete", variant="stop")
                with gr.Row():
                    pick = gr.Dropdown(label="Add agent", choices=ui_list_agents())
                    gr.Button("Add").click(on_add_agent, inputs=[grp, pick], outputs=[members])
                with gr.Row():
                    rm = gr.Dropdown(label="Remove agent", choices=ui_list_agents())
                    gr.Button("Remove").click(on_remove_agent, inputs=[grp, rm], outputs=[members])
                # Update roster on group change
                def _refresh_members(gid: str):
                    rows = [[k, n, d] for (k, n, d) in ui_group_members(gid)]
                    return rows
                grp.change(_refresh_members, inputs=[grp], outputs=[members])

            with gr.Column(scale=9):
                # Initialize chat with empty history (will load dynamically when group is selected)
                chat = gr.Chatbot(value=[], height=600, show_copy_button=True, avatar_images=(None, None))
                prompt = gr.Textbox(placeholder="Type @agent_key your message…", label="Message")
                send = gr.Button("Send", variant="primary")
                
                # Wire up send button and enter key
                send.click(on_send, inputs=[grp, prompt], outputs=[chat, prompt])
                prompt.submit(on_send, inputs=[grp, prompt], outputs=[chat, prompt])
                
                grp.change(load_history, inputs=[grp], outputs=[chat])

        # Wire up the delete button now that all components are created
        delete_btn.click(on_delete_group, inputs=[grp], outputs=[grp, members, chat])
        
        # Initialize everything when page loads
        async def on_app_load():
            await ensure_initialization()
            return on_refresh_groups()
        
        demo.load(on_app_load, outputs=[grp])

    return demo


APP = build_app()