# =========================================
# File: app/llm/openai_provider.py
# Purpose: Production-grade OpenAI provider with comprehensive functionality
# =========================================
from __future__ import annotations
import asyncio
import os
import json
from typing import List, Dict, Any, AsyncIterator, Optional
from src.core.llm.base import (
    LLM, LLMConfig, LLMMessage, LLMProvider, 
    LLMError, LLMConnectionError, LLMRateLimitError, LLMInvalidRequestError
)

try:
    from openai import OpenAI, AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    AsyncOpenAI = None
    OPENAI_AVAILABLE = False

class OpenAILLM(LLM):
    """Production-grade OpenAI LLM provider"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        
        if not OPENAI_AVAILABLE:
            raise LLMError("OpenAI library not available. Install with: pip install openai")
        
        api_key = config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise LLMError("OpenAI API key not provided")
            
        base_url = config.base_url or os.getenv("OPENAI_BASE_URL")
        
        # Initialize both sync and async clients
        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=config.timeout
        )
        self._async_client = AsyncOpenAI(
            api_key=api_key, 
            base_url=base_url,
            timeout=config.timeout
        )
        
    async def chat(self, messages: List[LLMMessage]) -> str:
        """Send chat completion request to OpenAI"""
        try:
            formatted_messages = self._format_messages_for_openai(messages)
            
            # Prepare completion parameters
            params = {
                "model": self.model,
                "messages": formatted_messages,
                "timeout": self.timeout
            }

            # Handle model-specific parameters
            if "gpt-5" in self.model:
                # GPT-5 uses max_completion_tokens and only supports default temperature
                params["max_completion_tokens"] = self.max_tokens
                # GPT-5 only supports temperature=1 (default), so we don't set it
            else:
                # Other models use max_tokens and support temperature configuration
                params["max_tokens"] = self.max_tokens
                params["temperature"] = self.temperature

            response = await self._async_client.chat.completions.create(**params)
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            raise self._handle_openai_error(e)
    
    async def chat_with_tools(self, messages: List[LLMMessage], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Chat completion with tool calling support"""
        try:
            formatted_messages = self._format_messages_for_openai(messages)
            formatted_tools = self._format_tools_for_openai(tools)
            
            # Prepare completion parameters
            params = {
                "model": self.model,
                "messages": formatted_messages,
                "tools": formatted_tools if formatted_tools else None,
                "tool_choice": "auto" if formatted_tools else None,
                "timeout": self.timeout
            }

            # Handle model-specific parameters
            if "gpt-5" in self.model:
                # GPT-5 uses max_completion_tokens and only supports default temperature
                params["max_completion_tokens"] = self.max_tokens
                # GPT-5 only supports temperature=1 (default), so we don't set it
            else:
                # Other models use max_tokens and support temperature configuration
                params["max_tokens"] = self.max_tokens
                params["temperature"] = self.temperature

            response = await self._async_client.chat.completions.create(**params)
            
            choice = response.choices[0]
            result = {
                "content": choice.message.content or "",
                "tool_calls": []
            }
            
            if choice.message.tool_calls:
                for tool_call in choice.message.tool_calls:
                    result["tool_calls"].append({
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": json.loads(tool_call.function.arguments)
                        }
                    })
            
            return result
            
        except Exception as e:
            raise self._handle_openai_error(e)
    
    async def stream_chat(self, messages: List[LLMMessage]) -> AsyncIterator[str]:
        """Stream chat completion response"""
        try:
            formatted_messages = self._format_messages_for_openai(messages)
            
            # Prepare streaming parameters
            stream_params = {
                "model": self.model,
                "messages": formatted_messages,
                "timeout": self.timeout,
                "stream": True
            }

            # Handle model-specific parameters
            if "gpt-5" in self.model:
                # GPT-5 uses max_completion_tokens and only supports default temperature
                stream_params["max_completion_tokens"] = self.max_tokens
                # GPT-5 only supports temperature=1 (default), so we don't set it
            else:
                # Other models use max_tokens and support temperature configuration
                stream_params["max_tokens"] = self.max_tokens
                stream_params["temperature"] = self.temperature

            stream = await self._async_client.chat.completions.create(**stream_params)
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            raise self._handle_openai_error(e)
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI embedding models"""
        try:
            # Use appropriate embedding model
            embedding_model = "text-embedding-3-small"  # More cost-effective
            if "large" in self.model.lower():
                embedding_model = "text-embedding-3-large"
            
            response = await self._async_client.embeddings.create(
                model=embedding_model,
                input=texts,
                timeout=self.timeout
            )
            
            return [data.embedding for data in response.data]
            
        except Exception as e:
            raise self._handle_openai_error(e)
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get OpenAI model information"""
        model_info = {
            "provider": "openai",
            "model": self.model,
            "supports_functions": True,
            "supports_streaming": True,
            "supports_embeddings": True,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        # Add model-specific info
        if "gpt-4" in self.model:
            model_info.update({
                "context_window": 128000 if "turbo" in self.model else 8192,
                "training_cutoff": "2023-12",
                "capabilities": ["text", "code", "reasoning"]
            })
        elif "gpt-3.5" in self.model:
            model_info.update({
                "context_window": 16385,
                "training_cutoff": "2021-09",
                "capabilities": ["text", "code"]
            })
        
        return model_info
    
    def _format_messages_for_openai(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """Convert LLMMessage objects to OpenAI format"""
        formatted = []
        for msg in messages:
            formatted.append({
                "role": msg.role,
                "content": msg.content  # content can be string or multimodal structure
            })
        return formatted
    
    def _format_tools_for_openai(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert tools to OpenAI format"""
        formatted_tools = []
        for tool in tools:
            if "function" in tool:
                formatted_tools.append({
                    "type": "function",
                    "function": tool["function"]
                })
        return formatted_tools
    
    def _handle_openai_error(self, error: Exception) -> LLMError:
        """Convert OpenAI errors to standardized LLM errors"""
        error_str = str(error).lower()
        
        if "rate limit" in error_str:
            return LLMRateLimitError(f"OpenAI rate limit exceeded: {error}")
        elif "invalid" in error_str or "bad request" in error_str:
            return LLMInvalidRequestError(f"Invalid OpenAI request: {error}")
        elif "connection" in error_str or "timeout" in error_str:
            return LLMConnectionError(f"OpenAI connection error: {error}")
        else:
            return LLMError(f"OpenAI error: {error}")
    
    @classmethod
    def create_from_settings(cls, settings) -> "OpenAILLM":
        """Create OpenAI LLM from settings object (backward compatibility)"""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model=getattr(settings, 'LLM_MODEL', 'gpt-4o-mini'),
            temperature=getattr(settings, 'LLM_TEMPERATURE', 0.2),
            max_tokens=getattr(settings, 'LLM_MAX_TOKENS', 4096),
            api_key=getattr(settings, 'OPENAI_API_KEY', None)
        )
        return cls(config)

