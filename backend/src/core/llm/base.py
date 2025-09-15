# =========================================
# File: app/llm/base.py
# Purpose: Production-grade LLM interface with comprehensive capabilities
# =========================================
from __future__ import annotations
import abc
from typing import List, Dict, Any, Optional, AsyncIterator, Union
from enum import Enum
from dataclasses import dataclass

class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"

@dataclass
class LLMMessage:
    """Standardized message format for all LLM providers"""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class LLMConfig:
    """LLM configuration parameters"""
    provider: LLMProvider
    model: str
    temperature: float = 0.2
    max_tokens: int = 4096
    timeout: float = 30.0
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    
class LLMError(Exception):
    """Base exception for LLM-related errors"""
    pass

class LLMConnectionError(LLMError):
    """Connection-related LLM errors"""
    pass

class LLMRateLimitError(LLMError):
    """Rate limit exceeded errors"""
    pass

class LLMInvalidRequestError(LLMError):
    """Invalid request errors"""
    pass

class LLM(abc.ABC):
    """Base class for all LLM providers with comprehensive functionality"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.provider = config.provider
        self.model = config.model
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.timeout = config.timeout
        
    @abc.abstractmethod
    async def chat(self, messages: List[LLMMessage]) -> str:
        """
        Send chat completion request and return response text
        Args:
            messages: List of messages in conversation
        Returns:
            Response text from the model
        Raises:
            LLMError: For various LLM-related errors
        """
        raise NotImplementedError
    
    @abc.abstractmethod
    async def chat_with_tools(self, messages: List[LLMMessage], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send chat completion with tool calling capability
        Args:
            messages: List of messages in conversation
            tools: Available tools for function calling
        Returns:
            Dict containing response and tool calls if any
        """
        raise NotImplementedError
    
    @abc.abstractmethod
    async def stream_chat(self, messages: List[LLMMessage]) -> AsyncIterator[str]:
        """
        Stream chat completion response
        Args:
            messages: List of messages in conversation
        Yields:
            Chunks of response text as they arrive
        """
        raise NotImplementedError
    
    @abc.abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for given texts
        Args:
            texts: List of texts to embed
        Returns:
            List of embedding vectors
        """
        raise NotImplementedError
    
    @abc.abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model
        Returns:
            Dict with model capabilities and limits
        """
        raise NotImplementedError
    
    async def simple_chat(self, system: str, user: str) -> str:
        """
        Simple chat interface for backward compatibility
        Args:
            system: System message
            user: User message
        Returns:
            Response text
        """
        messages = []
        if system:
            messages.append(LLMMessage(role="system", content=system))
        messages.append(LLMMessage(role="user", content=user))
        return await self.chat(messages)
    
    def format_messages(self, messages: List[Union[Dict[str, str], LLMMessage]]) -> List[LLMMessage]:
        """
        Convert various message formats to standardized LLMMessage format
        Args:
            messages: Messages in various formats
        Returns:
            List of LLMMessage objects
        """
        formatted = []
        for msg in messages:
            if isinstance(msg, dict):
                formatted.append(LLMMessage(
                    role=msg.get("role", "user"),
                    content=msg.get("content", ""),
                    metadata=msg.get("metadata")
                ))
            elif isinstance(msg, LLMMessage):
                formatted.append(msg)
            else:
                # Assume it's a string for user message
                formatted.append(LLMMessage(role="user", content=str(msg)))
        return formatted
        
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the LLM provider is accessible and healthy
        Returns:
            Dict with health status information
        """
        try:
            # Simple test call
            response = await self.simple_chat("You are a test.", "Respond with 'OK' only.")
            return {
                "healthy": True,
                "provider": self.provider.value,
                "model": self.model,
                "response_received": bool(response),
                "test_response": response[:50] if response else None
            }
        except Exception as e:
            return {
                "healthy": False,
                "provider": self.provider.value,
                "model": self.model,
                "error": str(e),
                "error_type": type(e).__name__
            }