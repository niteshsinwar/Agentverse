# =========================================
# File: app/llm/claude_provider.py
# Purpose: Production-grade Claude provider with comprehensive functionality
# =========================================
from __future__ import annotations
import os
import json
import asyncio
from typing import List, Dict, Any, AsyncIterator, Optional
from src.core.llm.base import (
    LLM, LLMConfig, LLMMessage, LLMProvider,
    LLMError, LLMConnectionError, LLMRateLimitError, LLMInvalidRequestError
)

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    try:
        import httpx
        HTTPX_AVAILABLE = True
    except ImportError:
        HTTPX_AVAILABLE = False

class ClaudeLLM(LLM):
    """Production-grade Claude LLM provider"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        
        if not ANTHROPIC_AVAILABLE and not HTTPX_AVAILABLE:
            raise LLMError("Neither Anthropic SDK nor httpx available. Install with: pip install anthropic httpx")
        
        api_key = config.api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        if not api_key:
            raise LLMError("Claude API key not provided")
        
        self.api_key = api_key
        self.base_url = config.base_url or "https://api.anthropic.com"
        
        if ANTHROPIC_AVAILABLE:
            self._client = anthropic.AsyncAnthropic(
                api_key=api_key,
                base_url=self.base_url,
                timeout=config.timeout
            )
    
    async def chat(self, messages: List[LLMMessage]) -> str:
        """Send chat completion request to Claude API"""
        try:
            if ANTHROPIC_AVAILABLE:
                return await self._chat_with_anthropic(messages)
            else:
                return await self._chat_with_httpx(messages)
        except Exception as e:
            raise self._handle_claude_error(e)
    
    async def chat_with_tools(self, messages: List[LLMMessage], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Chat completion with tool calling support"""
        try:
            if ANTHROPIC_AVAILABLE:
                # Claude supports function calling
                formatted_messages = self._format_messages_for_claude(messages)
                formatted_tools = self._format_tools_for_claude(tools)
                
                response = await self._client.messages.create(
                    model=self.model,
                    messages=formatted_messages,
                    tools=formatted_tools if formatted_tools else None,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
                
                result = {
                    "content": "",
                    "tool_calls": []
                }
                
                for content_block in response.content:
                    if hasattr(content_block, 'text'):
                        result["content"] += content_block.text
                    elif hasattr(content_block, 'tool_use'):
                        tool_use = content_block.tool_use
                        result["tool_calls"].append({
                            "id": tool_use.id,
                            "type": "function",
                            "function": {
                                "name": tool_use.name,
                                "arguments": tool_use.input
                            }
                        })
                
                return result
            else:
                # Fallback without tool support
                response = await self.chat(messages)
                return {
                    "content": response,
                    "tool_calls": []
                }
        except Exception as e:
            raise self._handle_claude_error(e)
    
    async def stream_chat(self, messages: List[LLMMessage]) -> AsyncIterator[str]:
        """Stream chat completion response"""
        try:
            if ANTHROPIC_AVAILABLE:
                formatted_messages = self._format_messages_for_claude(messages)
                
                async with self._client.messages.stream(
                    model=self.model,
                    messages=formatted_messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                ) as stream:
                    async for text in stream.text_stream:
                        yield text
            else:
                # Fallback to non-streaming
                response = await self.chat(messages)
                yield response
        except Exception as e:
            raise self._handle_claude_error(e)
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Claude doesn't provide embedding models, return mock embeddings"""
        # Claude doesn't have embedding models, so we return zeros or raise an error
        raise LLMError("Claude does not provide embedding models. Use OpenAI or Gemini for embeddings.")
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get Claude model information"""
        context_windows = {
            "claude-3-5-sonnet-20241022": 200000,
            "claude-3-5-sonnet-20240620": 200000,
            "claude-3-5-haiku-20241022": 200000,
            "claude-3-opus-20240229": 200000,
            "claude-3-sonnet-20240229": 200000,
            "claude-3-haiku-20240307": 200000
        }
        
        return {
            "provider": "claude",
            "model": self.model,
            "supports_functions": ANTHROPIC_AVAILABLE,
            "supports_streaming": ANTHROPIC_AVAILABLE,
            "supports_embeddings": False,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "context_window": context_windows.get(self.model, 200000),
            "capabilities": ["text", "images", "code", "reasoning", "analysis"]
        }
    
    async def _chat_with_anthropic(self, messages: List[LLMMessage]) -> str:
        """Chat using official Anthropic SDK"""
        formatted_messages = self._format_messages_for_claude(messages)
        
        response = await self._client.messages.create(
            model=self.model,
            messages=formatted_messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        
        # Concatenate all text blocks
        result = ""
        for content_block in response.content:
            if hasattr(content_block, 'text'):
                result += content_block.text
        
        return result
    
    async def _chat_with_httpx(self, messages: List[LLMMessage]) -> str:
        """Chat using direct HTTP calls"""
        formatted_messages = self._format_messages_for_claude(messages)
        
        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/messages",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extract text from content blocks
            text = ""
            if "content" in result:
                for block in result["content"]:
                    if block.get("type") == "text":
                        text += block.get("text", "")
            
            return text
    
    def _format_messages_for_claude(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """Convert LLMMessage objects to Claude format"""
        formatted = []
        system_message = None
        
        for msg in messages:
            if msg.role == "system":
                # Claude handles system messages separately
                system_message = msg.content
            elif msg.role == "assistant":
                formatted.append({
                    "role": "assistant",
                    "content": msg.content
                })
            else:  # user or other roles
                formatted.append({
                    "role": "user", 
                    "content": msg.content
                })
        
        # If we have a system message, prepend it to the first user message
        if system_message and formatted:
            for msg in formatted:
                if msg["role"] == "user":
                    msg["content"] = f"System: {system_message}\n\nUser: {msg['content']}"
                    break
        
        return formatted
    
    def _format_tools_for_claude(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert tools to Claude format"""
        if not ANTHROPIC_AVAILABLE:
            return []
        
        formatted_tools = []
        for tool in tools:
            if "function" in tool:
                func_def = tool["function"]
                formatted_tools.append({
                    "name": func_def.get("name", ""),
                    "description": func_def.get("description", ""),
                    "input_schema": func_def.get("parameters", {})
                })
        return formatted_tools
    
    def _handle_claude_error(self, error: Exception) -> LLMError:
        """Convert Claude errors to standardized LLM errors"""
        error_str = str(error).lower()
        
        if "rate limit" in error_str or "429" in error_str:
            return LLMRateLimitError(f"Claude rate limit exceeded: {error}")
        elif "invalid" in error_str or "400" in error_str:
            return LLMInvalidRequestError(f"Invalid Claude request: {error}")
        elif "connection" in error_str or "timeout" in error_str:
            return LLMConnectionError(f"Claude connection error: {error}")
        else:
            return LLMError(f"Claude error: {error}")
    
    @classmethod
    def create_from_settings(cls, settings) -> "ClaudeLLM":
        """Create Claude LLM from settings object (backward compatibility)"""
        config = LLMConfig(
            provider=LLMProvider.CLAUDE,
            model=getattr(settings, 'LLM_MODEL', 'claude-3-5-sonnet-20241022'),
            temperature=getattr(settings, 'LLM_TEMPERATURE', 0.2),
            max_tokens=getattr(settings, 'LLM_MAX_TOKENS', 4096),
            api_key=os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        )
        return cls(config)