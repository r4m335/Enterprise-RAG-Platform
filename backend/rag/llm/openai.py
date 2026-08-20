import os
from typing import List, Dict, Optional
from loguru import logger
from openai import AsyncOpenAI

from core.config import settings
from .base import LLMProvider, LLMResponse

class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.default_model = settings.LLM_MODEL
        
    async def generate(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        
        target_model = model or self.default_model
        
        if max_tokens is None:
            max_tokens = settings.LLM_MAX_TOKENS
            
        logger.debug(f"Calling OpenAI API with model {target_model}")
        
        response = await self.client.chat.completions.create(
            model=target_model,
            messages=messages, # type: ignore
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        content = response.choices[0].message.content or ""
        usage = response.usage
        
        return LLMResponse(
            content=content,
            model=target_model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0
        )
