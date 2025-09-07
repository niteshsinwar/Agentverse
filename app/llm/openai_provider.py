# =========================================
# File: app/llm/openai_provider.py
# Purpose: OpenAI provider (async via thread offload)
# =========================================
from __future__ import annotations
import asyncio
from typing import Optional
from app.llm.base import LLM
from app.config.settings import settings

try:
    from openai import OpenAI  # pip install openai>=1.0.0
except Exception:  # library missing in some envs
    OpenAI = None  # type: ignore


class OpenAILLM(LLM):
    def __init__(self, model: Optional[str] = None, temperature: float = 0.2, max_tokens: int = 4096) -> None:
        self.model = model or settings.LLM_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = OpenAI() if OpenAI else None

    async def chat(self, system: str, user: str) -> str:
        # Fallback if SDK is unavailable or key missing
        if not self._client or not settings.OPENAI_API_KEY:
            return f"[LLM disabled] system: {system[:60]}… | user: {user[:120]}…"

        def _call():
            resp = self._client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return resp.choices[0].message.content or ""

        return await asyncio.to_thread(_call)

