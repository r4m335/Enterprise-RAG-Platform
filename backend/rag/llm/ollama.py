import httpx
from typing import List, Dict, Optional
from loguru import logger
from core.config import settings
from .base import LLMProvider, LLMResponse

class OllamaProvider(LLMProvider):
    def __init__(self):
        self.api_url = settings.OLLAMA_URL.strip() if settings.OLLAMA_URL else "https://ollama.com/api/chat"
        self.api_key = settings.OLLAMA_API_KEY.strip() if settings.OLLAMA_API_KEY else ""
        self.default_model = settings.OLLAMA_MODEL.strip() if settings.OLLAMA_MODEL else "gpt-oss:20b"
        self.timeout = 60.0

    async def generate(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        target_model = model or self.default_model
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": target_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        logger.info(f"Calling Ollama Cloud ({self.api_url}) with model: {target_model}")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(self.api_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        content = data.get("message", {}).get("content", "")
        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)
        total_tokens = prompt_tokens + completion_tokens

        return LLMResponse(
            content=content,
            model=f"ollama:{target_model}",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens
        )
