
# =========================================
# File: app/llm/factory.py
# Purpose: Factory that returns the configured provider
# =========================================
from __future__ import annotations
from app.config.settings import settings
from app.llm.openai_provider import OpenAILLM
from app.llm.base import LLM


def get_llm() -> LLM:
    provider = (settings.LLM_PROVIDER or "openai").lower()
    if provider == "openai":
        return OpenAILLM(model=settings.LLM_MODEL, temperature=settings.LLM_TEMPERATURE, max_tokens=settings.LLM_MAX_TOKENS)
    # Add other providers here (gemini, etc.)
    return OpenAILLM(model=settings.LLM_MODEL, temperature=settings.LLM_TEMPERATURE, max_tokens=settings.LLM_MAX_TOKENS)

