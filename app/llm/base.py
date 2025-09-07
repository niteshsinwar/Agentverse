# =========================================
# File: app/llm/base.py
# Purpose: LLM interface
# =========================================
from __future__ import annotations
import abc

class LLM(abc.ABC):
    @abc.abstractmethod
    async def chat(self, system: str, user: str) -> str:  # returns plain text
        raise NotImplementedError