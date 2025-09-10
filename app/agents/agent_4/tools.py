from __future__ import annotations
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.agents.base_agent import agent_tool
from app.config.settings import settings

# Agent_4 (CrashLens) is designed to analyze documents through LLM capabilities
# No custom tools needed - document context is automatically provided by the orchestrator
