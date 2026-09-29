import os
from typing import List, Dict, Optional
from loguru import logger
from openai import AsyncOpenAI

from core.config import settings
from .base import LLMProvider, LLMResponse

class OpenAIProvider(LLMProvider):
    def __init__(self):
        api_key = settings.OPENAI_API_KEY.strip() if settings.OPENAI_API_KEY else ""
        if api_key:
            self.client = AsyncOpenAI(api_key=api_key)
        else:
            self.client = None
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
            
        if not self.client:
            logger.warning("OPENAI_API_KEY not configured. Falling back to extractive context presentation.")
            user_content = ""
            for m in reversed(messages):
                if m.get("role") == "user":
                    user_content = m.get("content", "")
                    break
            
            # Format retrieved context
            if "RETRIEVED DOCUMENTS" in user_content:
                parts = user_content.split("CURRENT QUESTION")
                docs_part = parts[0].replace("RETRIEVED DOCUMENTS", "").strip()
                question_part = parts[1].strip() if len(parts) > 1 else ""
                
                content = (
                    f"*(Note: `OPENAI_API_KEY` is not set in `.env`. Displaying top retrieved context excerpts from your documents below.)*\n\n"
                    f"**Extracted Context for:** *\"{question_part}\"*\n\n"
                    f"{docs_part}"
                )
            else:
                content = (
                    "*(Note: `OPENAI_API_KEY` is not configured in `.env`. Please add your OpenAI or OpenRouter API key in `.env` to enable AI synthesis.)*\n\n"
                    "No relevant document context found."
                )
                
            return LLMResponse(
                content=content,
                model="extractive-fallback",
                prompt_tokens=len(user_content) // 4,
                completion_tokens=len(content) // 4,
                total_tokens=(len(user_content) + len(content)) // 4
            )
            
        logger.debug(f"Calling OpenAI API with model {target_model}")
        
        try:
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
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            fallback_text = (
                f"*(Note: OpenAI API call returned an error: `{str(e)}`)*\n\n"
                f"Please verify your `OPENAI_API_KEY` in `.env`."
            )
            return LLMResponse(
                content=fallback_text,
                model=target_model,
                prompt_tokens=0,
                completion_tokens=len(fallback_text) // 4,
                total_tokens=len(fallback_text) // 4
            )
