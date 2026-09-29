def get_llm_provider():
    from core.config import settings
    
    provider_name = (settings.LLM_PROVIDER or "").lower().strip()
    
    if provider_name in ("ollama", "fallback", "chain", "multi"):
        from .fallback_chain import FallbackLLMProvider
        return FallbackLLMProvider()
    elif provider_name == "ollama_direct":
        from .ollama import OllamaProvider
        return OllamaProvider()
    elif provider_name == "openai":
        from .openai import OpenAIProvider
        return OpenAIProvider()
    elif provider_name == "fake":
        from .fake import FakeLLMProvider
        return FakeLLMProvider()
    else:
        # Default to robust fallback chain with Ollama Cloud first
        from .fallback_chain import FallbackLLMProvider
        return FallbackLLMProvider()
