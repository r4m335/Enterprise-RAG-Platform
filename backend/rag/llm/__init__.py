def get_llm_provider():
    from core.config import settings
    
    if settings.LLM_PROVIDER == "openai":
        from .openai import OpenAIProvider
        return OpenAIProvider()
    elif settings.LLM_PROVIDER == "fake":
        from .fake import FakeLLMProvider
        return FakeLLMProvider()
    else:
        raise ValueError(f"Unknown LLM Provider: {settings.LLM_PROVIDER}")
