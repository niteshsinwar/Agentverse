# =========================================
# File: src/core/llm/factory.py
# Purpose: LangChain-based LLM factory - unified interface for all providers
# =========================================
from __future__ import annotations

import os
from typing import Any, Dict, Optional

# LangChain unified LLM imports
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain_core.runnables import RunnableWithFallbacks

from src.core.config.settings import get_settings

settings = get_settings()


class LLM:
    """
    Unified LLM interface using LangChain.

    Benefits:
    - Automatic retries with exponential backoff
    - Rate limiting
    - Token counting
    - Streaming support
    - Structured outputs
    - Multi-provider support (OpenAI, Claude, Gemini, etc.)
    - Battle-tested by LangChain community
    """

    def __init__(self, langchain_llm: BaseChatModel, provider: str, model: str):
        self.langchain_llm = langchain_llm
        self.provider = provider
        self.model = model

    async def simple_chat(self, system: str, user: str) -> str:
        """
        Simple chat interface (backward compatible with existing code).

        Args:
            system: System prompt
            user: User message

        Returns:
            AI response as string
        """
        messages = [
            SystemMessage(content=system),
            HumanMessage(content=user)
        ]

        response = await self.langchain_llm.ainvoke(messages)
        return response.content

    async def chat(self, messages: list) -> str:
        """
        Chat with message history.

        Args:
            messages: List of messages (dicts or LangChain Message objects)

        Returns:
            AI response as string
        """
        # Convert to LangChain messages if needed
        langchain_messages = []

        for msg in messages:
            if isinstance(msg, BaseMessage):
                langchain_messages.append(msg)
            elif isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")

                if role == "system":
                    langchain_messages.append(SystemMessage(content=content))
                elif role == "user":
                    langchain_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    langchain_messages.append(AIMessage(content=content))
            else:
                # Assume it's a message object with role and content attributes
                if hasattr(msg, "role") and hasattr(msg, "content"):
                    if msg.role == "system":
                        langchain_messages.append(SystemMessage(content=msg.content))
                    elif msg.role == "user":
                        langchain_messages.append(HumanMessage(content=msg.content))
                    elif msg.role == "assistant":
                        langchain_messages.append(AIMessage(content=msg.content))

        response = await self.langchain_llm.ainvoke(langchain_messages)
        return response.content

    async def chat_stream(self, messages: list):
        """
        Stream chat responses.

        Args:
            messages: List of messages

        Yields:
            Response chunks
        """
        langchain_messages = self._convert_to_langchain_messages(messages)

        async for chunk in self.langchain_llm.astream(langchain_messages):
            if hasattr(chunk, 'content'):
                yield chunk.content

    async def chat_with_tools(self, messages: list, tools: list) -> dict:
        """
        Chat with tool calling support.

        Args:
            messages: List of messages
            tools: List of tool definitions

        Returns:
            Dict with content and tool_calls
        """
        langchain_messages = self._convert_to_langchain_messages(messages)

        # LangChain handles tool binding automatically
        llm_with_tools = self.langchain_llm.bind_tools(tools)
        response = await llm_with_tools.ainvoke(langchain_messages)

        result = {
            "content": response.content or "",
            "tool_calls": []
        }

        # Extract tool calls if present
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tool_call in response.tool_calls:
                result["tool_calls"].append({
                    "id": tool_call.get("id", ""),
                    "type": tool_call.get("type", "function"),
                    "function": {
                        "name": tool_call.get("name", ""),
                        "arguments": tool_call.get("args", {})
                    }
                })

        return result

    async def embed_texts(self, texts: list) -> list:
        """
        Generate embeddings for texts.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        # LangChain embeddings support
        if self.provider == "openai":
            from langchain_openai import OpenAIEmbeddings
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            return await embeddings.aembed_documents(texts)

        elif self.provider == "claude":
            # Claude doesn't have native embeddings, use Voyage AI or similar
            raise NotImplementedError("Claude embeddings not yet supported. Use OpenAI or Gemini.")

        elif self.provider == "gemini":
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            return await embeddings.aembed_documents(texts)

        else:
            raise ValueError(f"Embeddings not supported for provider: {self.provider}")

    def _convert_to_langchain_messages(self, messages: list) -> list:
        """Convert various message formats to LangChain messages"""
        langchain_messages = []

        for msg in messages:
            if isinstance(msg, BaseMessage):
                langchain_messages.append(msg)
            elif isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")

                if role == "system":
                    langchain_messages.append(SystemMessage(content=content))
                elif role == "user":
                    langchain_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    langchain_messages.append(AIMessage(content=content))

        return langchain_messages

    async def health_check(self) -> Dict[str, Any]:
        """
        Check if LLM is accessible and working.

        Returns:
            Health status dict
        """
        try:
            response = await self.simple_chat(
                system="You are a helpful assistant.",
                user="Say 'OK' if you can read this."
            )

            return {
                "healthy": True,
                "provider": self.provider,
                "model": self.model,
                "response": response
            }
        except Exception as e:
            return {
                "healthy": False,
                "provider": self.provider,
                "model": self.model,
                "error": str(e),
                "error_type": type(e).__name__
            }


def get_llm(provider: Optional[str] = None, model: Optional[str] = None, **kwargs: Any) -> LLM:
    """
    Get LLM instance using LangChain.

    Args:
        provider: LLM provider (openai, claude, gemini)
        model: Model name
        **kwargs: Additional config (temperature, max_tokens, api_key, etc.)

    Returns:
        LLM instance

    Example:
        ```python
        llm = get_llm(provider="openai", model="gpt-4o-mini")
        response = await llm.simple_chat(
            system="You are helpful",
            user="Hello!"
        )
        ```
    """
    # Defaults
    provider_name = provider or settings.llm_provider or "openai"
    provider_name = provider_name.lower()

    # Default models per provider
    default_models = {
        "openai": "gpt-4o-mini",
        "claude": "claude-3-5-sonnet-20241022",
        "gemini": "gemini-1.5-flash"
    }

    model_name = model or getattr(settings, 'LLM_MODEL', default_models.get(provider_name, "gpt-4o-mini"))

    # Common parameters
    temperature = kwargs.get('temperature', getattr(settings, 'LLM_TEMPERATURE', 0.2))
    max_tokens = kwargs.get('max_tokens', getattr(settings, 'LLM_MAX_TOKENS', 4096))
    timeout = kwargs.get('timeout', 60.0)

    # Reasoning models (o1, o3, gpt-5) don't support custom temperature
    is_reasoning_model = any(x in model_name.lower() for x in ['o1', 'o3', 'gpt-5'])
    if is_reasoning_model:
        temperature = 1  # Reasoning models only support default temperature

    # API key resolution
    api_key_map = {
        "openai": "OPENAI_API_KEY",
        "claude": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY"
    }

    settings_key_map = {
        "openai": "openai_api_key",
        "claude": "anthropic_api_key",
        "gemini": "gemini_api_key"
    }

    api_key = (
        kwargs.get('api_key') or
        getattr(settings, settings_key_map.get(provider_name, ''), None) or
        os.getenv(api_key_map.get(provider_name, ''))
    )

    # Create LangChain LLM
    try:
        if provider_name == "openai":
            langchain_llm = ChatOpenAI(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
                api_key=api_key,
                max_retries=3  # LangChain automatic retries!
            )

        elif provider_name == "claude":
            langchain_llm = ChatAnthropic(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
                api_key=api_key,
                max_retries=3
            )

        elif provider_name == "gemini":
            langchain_llm = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                max_output_tokens=max_tokens,
                timeout=timeout,
                google_api_key=api_key
            )

        else:
            raise ValueError(f"Unsupported provider: {provider_name}. Supported: openai, claude, gemini")

        # Wrap in our LLM interface
        return LLM(langchain_llm, provider_name, model_name)

    except Exception as e:
        # Try fallback if configured
        fallback_provider = kwargs.get("fallback_provider") or getattr(settings.llm, 'fallback_provider', None)

        if fallback_provider and fallback_provider != provider_name:
            print(f"⚠️ Primary provider {provider_name} failed: {e}")
            print(f"🔄 Trying fallback provider: {fallback_provider}")

            # Remove fallback_provider from kwargs to avoid infinite recursion
            fallback_kwargs = {k: v for k, v in kwargs.items() if k != 'fallback_provider'}

            try:
                return get_llm(provider=fallback_provider, model=None, **fallback_kwargs)
            except Exception as fallback_error:
                raise Exception(
                    f"Both primary provider '{provider_name}' and fallback '{fallback_provider}' failed. "
                    f"Primary: {e}, Fallback: {fallback_error}"
                )

        # No fallback or fallback also failed
        raise


def get_llm_from_settings() -> LLM:
    """
    Get LLM using current settings (backward compatibility).

    Returns:
        LLM instance
    """
    return get_llm()


def list_available_providers() -> Dict[str, Dict[str, Any]]:
    """
    List all available LLM providers.

    Returns:
        Dict of provider info
    """
    providers = {}

    provider_info = {
        "openai": {
            "name": "OpenAI",
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            "capabilities": ["chat", "tools", "streaming", "structured_output", "vision"],
            "requires": ["OPENAI_API_KEY"]
        },
        "claude": {
            "name": "Anthropic Claude",
            "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
            "capabilities": ["chat", "tools", "streaming", "structured_output", "vision"],
            "requires": ["ANTHROPIC_API_KEY"]
        },
        "gemini": {
            "name": "Google Gemini",
            "models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"],
            "capabilities": ["chat", "tools", "streaming", "vision", "long_context"],
            "requires": ["GEMINI_API_KEY"]
        }
    }

    for provider_key, info in provider_info.items():
        # Check if provider is available
        available = False
        error = None

        try:
            if provider_key == "openai":
                import openai
                available = True
            elif provider_key == "claude":
                import anthropic
                available = True
            elif provider_key == "gemini":
                import google.generativeai
                available = True
        except ImportError as e:
            error = f"Missing package: {e}"

        providers[provider_key] = {
            **info,
            "available": available,
            "error": error
        }

    return providers


async def health_check_all_providers() -> Dict[str, Dict[str, Any]]:
    """
    Health check all available providers.

    Returns:
        Dict of health status for each provider
    """
    results = {}

    for provider_key in ["openai", "claude", "gemini"]:
        try:
            llm = get_llm(provider=provider_key)
            health = await llm.health_check()
            results[provider_key] = health
        except Exception as e:
            results[provider_key] = {
                "healthy": False,
                "provider": provider_key,
                "error": str(e),
                "error_type": type(e).__name__
            }

    return results


# Backward compatibility exports
LLMProvider = None  # Not needed anymore - LangChain handles provider abstraction
LLMConfig = None  # Not needed anymore - LangChain handles configuration
LLMError = Exception  # Use standard Exception
