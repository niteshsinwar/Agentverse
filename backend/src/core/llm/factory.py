
# =========================================
# File: app/llm/factory.py
# Purpose: Production-grade LLM factory supporting all providers
# =========================================
from __future__ import annotations
import os
from typing import Optional, Dict, Any
from src.core.config.settings import get_settings; settings = get_settings()
from src.core.llm.base import LLM, LLMConfig, LLMProvider, LLMError

# Import all providers
from src.core.llm.openai_provider import OpenAILLM
from src.core.llm.gemini_provider import GeminiLLM
from src.core.llm.claude_provider import ClaudeLLM

# Provider registry
PROVIDER_CLASSES = {
    LLMProvider.OPENAI: OpenAILLM,
    LLMProvider.GEMINI: GeminiLLM,
    LLMProvider.CLAUDE: ClaudeLLM
}

def get_llm(provider: Optional[str] = None, model: Optional[str] = None, **kwargs) -> LLM:
    """
    Get LLM instance based on configuration
    Args:
        provider: Override provider from settings
        model: Override model from settings 
        **kwargs: Additional config parameters
    Returns:
        Configured LLM instance
    Raises:
        LLMError: If provider is not supported or configuration is invalid
    """
    provider_name = provider or settings.llm_provider or "openai"
    fallback_name = kwargs.pop("fallback_provider", None) or settings.llm.fallback_provider

    def instantiate(provider_str: str) -> LLM:
        try:
            provider_enum_local = LLMProvider(provider_str.lower())
        except ValueError:
            raise LLMError(f"Unsupported LLM provider: {provider_str}. Supported: {[p.value for p in LLMProvider]}")
        config_local = create_llm_config(provider_enum_local, model, **kwargs)
        provider_class_local = PROVIDER_CLASSES[provider_enum_local]
        return provider_class_local(config_local)

    # Try primary, then fallback if configured
    try:
        return instantiate(provider_name)
    except Exception as primary_error:
        if fallback_name and fallback_name.lower() != provider_name.lower():
            try:
                return instantiate(fallback_name)
            except Exception as fallback_error:
                raise LLMError(
                    f"Both primary provider '{provider_name}' and fallback '{fallback_name}' failed. "
                    f"Primary error: {primary_error}; Fallback error: {fallback_error}"
                )
        raise

def create_llm_config(provider: LLMProvider, model: Optional[str] = None, **kwargs) -> LLMConfig:
    """
    Create LLM configuration with proper defaults for each provider
    Args:
        provider: LLM provider enum
        model: Model name override
        **kwargs: Additional config parameters
    Returns:
        LLM configuration object
    """
    # Default models for each provider
    default_models = {
        LLMProvider.OPENAI: "gpt-4o-mini",
        LLMProvider.GEMINI: "gemini-1.5-flash",
        LLMProvider.CLAUDE: "claude-3-5-sonnet-20241022"
    }
    
    # Default API key environment variables
    api_key_env_vars = {
        LLMProvider.OPENAI: "OPENAI_API_KEY",
        LLMProvider.GEMINI: "GEMINI_API_KEY", 
        LLMProvider.CLAUDE: "ANTHROPIC_API_KEY"
    }
    
    # Get configuration values
    model_name = model or getattr(settings, 'LLM_MODEL', default_models[provider])
    temperature = kwargs.get('temperature', getattr(settings, 'LLM_TEMPERATURE', 0.2))
    max_tokens = kwargs.get('max_tokens', getattr(settings, 'LLM_MAX_TOKENS', 4096))
    timeout = kwargs.get('timeout', 30.0)
    api_key = kwargs.get('api_key') or os.getenv(api_key_env_vars[provider])
    base_url = kwargs.get('base_url')
    
    return LLMConfig(
        provider=provider,
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        api_key=api_key,
        base_url=base_url
    )

def get_llm_from_settings() -> LLM:
    """
    Get LLM using current settings (backward compatibility)
    Returns:
        Configured LLM instance
    """
    return get_llm()

def list_available_providers() -> Dict[str, Dict[str, Any]]:
    """
    List all available LLM providers and their status
    Returns:
        Dict of provider info including availability and requirements
    """
    providers = {}
    
    for provider in LLMProvider:
        provider_info = {
            "name": provider.value,
            "available": False,
            "requirements": [],
            "models": [],
            "capabilities": []
        }
        
        try:
            # Try to create a test config to check availability
            config = create_llm_config(provider)
            provider_class = PROVIDER_CLASSES[provider]
            
            # Check if required dependencies are available
            if provider == LLMProvider.OPENAI:
                try:
                    import openai
                    provider_info["available"] = True
                    provider_info["requirements"] = ["openai>=1.0.0"]
                    provider_info["models"] = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
                    provider_info["capabilities"] = ["chat", "tools", "streaming", "embeddings"]
                except ImportError:
                    provider_info["requirements"] = ["pip install openai"]
            
            elif provider == LLMProvider.GEMINI:
                try:
                    import google.generativeai
                    provider_info["available"] = True
                    provider_info["requirements"] = ["google-generativeai"]
                    provider_info["models"] = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"]
                    provider_info["capabilities"] = ["chat", "tools", "streaming", "embeddings", "vision"]
                except ImportError:
                    provider_info["requirements"] = ["pip install google-generativeai"]
            
            elif provider == LLMProvider.CLAUDE:
                try:
                    import anthropic
                    provider_info["available"] = True
                    provider_info["requirements"] = ["anthropic"]
                    provider_info["models"] = ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"]
                    provider_info["capabilities"] = ["chat", "tools", "streaming", "vision"]
                except ImportError:
                    provider_info["requirements"] = ["pip install anthropic"]
        
        except Exception as e:
            provider_info["error"] = str(e)
        
        providers[provider.value] = provider_info
    
    return providers

async def health_check_all_providers() -> Dict[str, Dict[str, Any]]:
    """
    Health check all available providers
    Returns:
        Dict of health status for each provider
    """
    results = {}
    
    for provider in LLMProvider:
        try:
            llm = get_llm(provider.value)
            health = await llm.health_check()
            results[provider.value] = health
        except Exception as e:
            results[provider.value] = {
                "healthy": False,
                "provider": provider.value,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    return results

