# =========================================
# File: app/telemetry/context.py
# Purpose: ContextVars to enrich logs/events with group/agent context
# =========================================
import contextvars
from typing import Optional, Dict

group_id_var = contextvars.ContextVar("group_id", default="")
agent_key_var = contextvars.ContextVar("agent_key", default="")


def set_context(group_id: Optional[str] = None, agent_key: Optional[str] = None):
    tokens = {}
    if group_id is not None:
        tokens["group_id"] = group_id_var.set(group_id)
    if agent_key is not None:
        tokens["agent_key"] = agent_key_var.set(agent_key)
    return tokens


def reset_context(tokens: Dict):
    if not tokens:
        return
    if "group_id" in tokens:
        group_id_var.reset(tokens["group_id"])
    if "agent_key" in tokens:
        agent_key_var.reset(tokens["agent_key"])        


def get_context() -> Dict[str, str]:
    return {"group_id": group_id_var.get(), "agent_key": agent_key_var.get()}
