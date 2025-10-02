# =========================================
# File: app/llm/gemini_provider.py
# Purpose: Production-grade Gemini provider with comprehensive functionality
# =========================================
from __future__ import annotations
import asyncio
import os
from typing import Any, AsyncIterator, Dict, List, Optional
from src.core.llm.base import (
    LLM,
    LLMConfig,
    LLMConnectionError,
    LLMError,
    LLMInvalidRequestError,
    LLMMessage,
    LLMProvider,
    LLMRateLimitError,
)

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    try:
        import httpx
        HTTPX_AVAILABLE = True
    except ImportError:
        HTTPX_AVAILABLE = False


class GeminiLLM(LLM):
    """Production-grade Gemini LLM provider"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        
        if not GENAI_AVAILABLE and not HTTPX_AVAILABLE:
            raise LLMError("Neither Google GenAI SDK nor httpx available. Install with: pip install google-generativeai httpx")
        
        api_key = config.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise LLMError("Gemini API key not provided")
        
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        
        if GENAI_AVAILABLE:
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(self.model)
        
    async def chat(self, messages: List[LLMMessage]) -> str:
        """Send chat completion request to Gemini API"""
        try:
            if GENAI_AVAILABLE:
                return await self._chat_with_genai(messages)
            else:
                return await self._chat_with_httpx(messages)
        except Exception as e:
            raise self._handle_gemini_error(e)
    
    async def chat_with_tools(self, messages: List[LLMMessage], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Chat completion with tool calling support"""
        try:
            if GENAI_AVAILABLE:
                # Gemini supports function calling
                formatted_tools = self._format_tools_for_gemini(tools)
                formatted_messages = self._format_messages_for_gemini(messages)
                
                def _sync_call():
                    model_with_tools = genai.GenerativeModel(
                        model_name=self.model,
                        tools=formatted_tools if formatted_tools else None
                    )
                    
                    response = model_with_tools.generate_content(
                        formatted_messages,
                        generation_config=genai.types.GenerationConfig(
                            temperature=self.temperature,
                            max_output_tokens=self.max_tokens
                        )
                    )
                    return response
                
                response = await asyncio.to_thread(_sync_call)
                
                result = {
                    "content": response.text if response.text else "",
                    "tool_calls": []
                }
                
                # Handle function calls if present
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'function_call'):
                                result["tool_calls"].append({
                                    "type": "function",
                                    "function": {
                                        "name": part.function_call.name,
                                        "arguments": dict(part.function_call.args)
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
            raise self._handle_gemini_error(e)
    
    async def stream_chat(self, messages: List[LLMMessage]) -> AsyncIterator[str]:
        """Stream chat completion response"""
        try:
            if GENAI_AVAILABLE:
                async for chunk in self._stream_with_genai(messages):
                    yield chunk
            else:
                # Fallback to non-streaming
                response = await self.chat(messages)
                yield response
        except Exception as e:
            raise self._handle_gemini_error(e)
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Gemini embedding models"""
        try:
            embeddings = []
            
            if GENAI_AVAILABLE:
                def _sync_embed():
                    result = []
                    for text in texts:
                        embedding = genai.embed_content(
                            model="models/text-embedding-004",
                            content=text
                        )
                        result.append(embedding['embedding'])
                    return result
                
                embeddings = await asyncio.to_thread(_sync_embed)
            else:
                # HTTP fallback
                for text in texts:
                    payload = {
                        "model": "models/text-embedding-004",
                        "content": {"parts": [{"text": text}]}
                    }
                    
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"{self.base_url}/models/text-embedding-004:embedContent",
                            params={"key": self.api_key},
                            json=payload,
                            headers={"Content-Type": "application/json"},
                            timeout=self.timeout
                        )
                        response.raise_for_status()
                        
                        result = response.json()
                        embedding = result.get("embedding", {}).get("values", [])
                        embeddings.append(embedding)
            
            return embeddings
        except Exception as e:
            raise self._handle_gemini_error(e)
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get Gemini model information"""
        return {
            "provider": "gemini",
            "model": self.model,
            "supports_functions": GENAI_AVAILABLE,
            "supports_streaming": GENAI_AVAILABLE,
            "supports_embeddings": True,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "context_window": 1000000 if "1.5" in self.model else 32000,
            "capabilities": ["text", "images", "code", "reasoning"]
        }
    
    async def _chat_with_genai(self, messages: List[LLMMessage]) -> str:
        """Chat using official Google GenAI SDK"""
        def _sync_call():
            formatted_messages = self._format_messages_for_gemini(messages)
            response = self._model.generate_content(
                formatted_messages,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens
                )
            )
            return response.text
        
        return await asyncio.to_thread(_sync_call)
    
    async def _chat_with_httpx(self, messages: List[LLMMessage]) -> str:
        """Chat using direct HTTP calls"""
        contents = []
        for msg in messages:
            role = "user" if msg.role == "user" else "model"
            if msg.role == "system":
                # Prepend system message to first user message
                if contents and contents[-1]["role"] == "user":
                    contents[-1]["parts"][0]["text"] = f"{msg.content}\n\n{contents[-1]['parts'][0]['text']}"
                else:
                    contents.append({
                        "role": "user",
                        "parts": [{"text": msg.content}]
                    })
            else:
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.content}]
                })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/models/{self.model}:generateContent",
                params={"key": self.api_key},
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "candidates" in result and len(result["candidates"]) > 0:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return "No response generated"
    
    async def _stream_with_genai(self, messages: List[LLMMessage]) -> AsyncIterator[str]:
        """Stream response using GenAI SDK"""
        def _sync_stream():
            formatted_messages = self._format_messages_for_gemini(messages)
            response = self._model.generate_content(
                formatted_messages,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens
                ),
                stream=True
            )
            return response
        
        stream = await asyncio.to_thread(_sync_stream)
        for chunk in stream:
            if chunk.text:
                yield chunk.text
    
    def _format_messages_for_gemini(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """Convert LLMMessage objects to Gemini format"""
        formatted = []
        for msg in messages:
            if msg.role == "system":
                # System messages become user messages with special formatting
                formatted.append({
                    "role": "user",
                    "parts": [f"System: {msg.content}"]
                })
            else:
                role = "user" if msg.role == "user" else "model"
                formatted.append({
                    "role": role,
                    "parts": [msg.content]
                })
        return formatted
    
    def _format_tools_for_gemini(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert tools to Gemini function calling format"""
        if not GENAI_AVAILABLE:
            return []
        
        formatted_tools = []
        for tool in tools:
            if "function" in tool:
                func_def = tool["function"]
                formatted_tools.append({
                    "function_declarations": [{
                        "name": func_def.get("name", ""),
                        "description": func_def.get("description", ""),
                        "parameters": func_def.get("parameters", {})
                    }]
                })
        return formatted_tools
    
    def _handle_gemini_error(self, error: Exception) -> LLMError:
        """Convert Gemini errors to standardized LLM errors"""
        error_str = str(error).lower()
        
        if "quota" in error_str or "rate limit" in error_str:
            return LLMRateLimitError(f"Gemini rate limit exceeded: {error}")
        elif "invalid" in error_str or "bad request" in error_str:
            return LLMInvalidRequestError(f"Invalid Gemini request: {error}")
        elif "connection" in error_str or "timeout" in error_str:
            return LLMConnectionError(f"Gemini connection error: {error}")
        else:
            return LLMError(f"Gemini error: {error}")
    
    @classmethod
    def create_from_settings(cls, settings) -> "GeminiLLM":
        """Create Gemini LLM from settings object (backward compatibility)"""
        config = LLMConfig(
            provider=LLMProvider.GEMINI,
            model=getattr(settings, 'LLM_MODEL', 'gemini-1.5-flash'),
            temperature=getattr(settings, 'LLM_TEMPERATURE', 0.2),
            max_tokens=getattr(settings, 'LLM_MAX_TOKENS', 4096),
            api_key=os.getenv("GEMINI_API_KEY")
        )
        return cls(config)
