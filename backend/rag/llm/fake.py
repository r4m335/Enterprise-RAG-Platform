from typing import List, Dict, Optional
from loguru import logger

from .base import LLMProvider, LLMResponse

class FakeLLMProvider(LLMProvider):
    def __init__(self):
        self.default_model = "fake-model"
        
    async def generate(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        
        target_model = model or self.default_model
        logger.debug(f"Calling FAKE LLM with model {target_model}")
        
        # Determine fake response logic
        content = "FAKE ANSWER"
        if messages and "password" in messages[-1]["content"].lower():
            content = "Employees must rotate passwords every 90 days."
        
        # Calculate deterministically based on input
        input_len = sum(len(m["content"]) for m in messages) // 4
        output_len = len(content) // 4
        
        return LLMResponse(
            content=content,
            model=target_model,
            prompt_tokens=input_len,
            completion_tokens=output_len,
            total_tokens=input_len + output_len
        )
