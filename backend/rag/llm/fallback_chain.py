import httpx
from typing import List, Dict, Optional, Any
from loguru import logger
from core.config import settings
from .base import LLMProvider, LLMResponse

class FallbackLLMProvider(LLMProvider):
    """
    Tiered LLM Provider with automatic fallback:
    1. Ollama Cloud (First Choice: gpt-oss:20b)
    2. Groq (llama-3.3-70b-versatile / llama-3.1-8b-instant)
    3. HuggingFace Router
    4. NVIDIA NIM
    5. Cloudflare Workers AI
    6. Pollinations AI
    7. OpenAI (gpt-4o-mini)
    8. Local Extractive Context Fallback (100% reliable guarantee)
    """

    def __init__(self):
        self.default_model = settings.LLM_MODEL
        self.timeout = 45.0

    async def _try_ollama(self, messages: List[Dict[str, str]], temperature: float, max_tokens: Optional[int]) -> Optional[LLMResponse]:
        if not settings.OLLAMA_API_KEY:
            return None
        url = settings.OLLAMA_URL or "https://ollama.com/api/chat"
        model = settings.OLLAMA_MODEL or "gpt-oss:20b"
        headers = {
            "Authorization": f"Bearer {settings.OLLAMA_API_KEY.strip()}",
            "Content-Type": "application/json"
        }
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature}
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        logger.info(f"[LLM Chain #1] Calling Ollama Cloud ({url}) with model: {model}")
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content = data.get("message", {}).get("content", "")
            if content:
                prompt_tokens = data.get("prompt_eval_count", 0)
                completion_tokens = data.get("eval_count", 0)
                return LLMResponse(
                    content=content,
                    model=f"ollama:{model}",
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens
                )
        return None

    async def _try_groq(self, messages: List[Dict[str, str]], temperature: float, max_tokens: Optional[int]) -> Optional[LLMResponse]:
        if not settings.GROQ_API_KEY:
            return None
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY.strip()}",
            "Content-Type": "application/json"
        }
        for model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
            try:
                logger.info(f"[LLM Chain #2] Calling Groq with model: {model}")
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens or 1000
                }
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        content = data["choices"][0]["message"]["content"]
                        usage = data.get("usage", {})
                        return LLMResponse(
                            content=content,
                            model=f"groq:{model}",
                            prompt_tokens=usage.get("prompt_tokens", 0),
                            completion_tokens=usage.get("completion_tokens", 0),
                            total_tokens=usage.get("total_tokens", 0)
                        )
            except Exception as e:
                logger.warning(f"Groq {model} attempt failed: {e}")
        return None

    async def _try_huggingface(self, messages: List[Dict[str, str]], temperature: float, max_tokens: Optional[int]) -> Optional[LLMResponse]:
        if not settings.HUGGINGFACE_API_KEY:
            return None
        models = ["Qwen/Qwen2.5-72B-Instruct", "meta-llama/Llama-3.2-3B-Instruct"]
        headers = {
            "Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY.strip()}",
            "Content-Type": "application/json"
        }
        for model in models:
            url = f"https://router.huggingface.co/hf-inference/models/{model}/v1/chat/completions"
            try:
                logger.info(f"[LLM Chain #3] Calling HuggingFace Router with model: {model}")
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens or 1000
                }
                async with httpx.AsyncClient(timeout=25.0) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        content = data["choices"][0]["message"]["content"]
                        usage = data.get("usage", {})
                        return LLMResponse(
                            content=content,
                            model=f"huggingface:{model}",
                            prompt_tokens=usage.get("prompt_tokens", 0),
                            completion_tokens=usage.get("completion_tokens", 0),
                            total_tokens=usage.get("total_tokens", 0)
                        )
            except Exception as e:
                logger.warning(f"HuggingFace {model} attempt failed: {e}")
        return None

    async def _try_nvidia(self, messages: List[Dict[str, str]], temperature: float, max_tokens: Optional[int]) -> Optional[LLMResponse]:
        if not settings.NVIDIA_API_KEY:
            return None
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.NVIDIA_API_KEY.strip()}",
            "Content-Type": "application/json"
        }
        for model in ["meta/llama-3.1-70b-instruct", "meta/llama-3.1-8b-instruct"]:
            try:
                logger.info(f"[LLM Chain #4] Calling NVIDIA NIM with model: {model}")
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens or 1000
                }
                async with httpx.AsyncClient(timeout=25.0) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        content = data["choices"][0]["message"]["content"]
                        usage = data.get("usage", {})
                        return LLMResponse(
                            content=content,
                            model=f"nvidia:{model}",
                            prompt_tokens=usage.get("prompt_tokens", 0),
                            completion_tokens=usage.get("completion_tokens", 0),
                            total_tokens=usage.get("total_tokens", 0)
                        )
            except Exception as e:
                logger.warning(f"NVIDIA {model} attempt failed: {e}")
        return None

    async def _try_cloudflare(self, messages: List[Dict[str, str]]) -> Optional[LLMResponse]:
        account_id = settings.CLOUDFLARE_ACCOUNT_ID.strip() if settings.CLOUDFLARE_ACCOUNT_ID else ""
        token = settings.CLOUDFLARE_API_TOKEN.strip() if settings.CLOUDFLARE_API_TOKEN else ""
        if not account_id or not token:
            return None
        model = "@cf/meta/llama-3.1-8b-instruct"
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        try:
            logger.info(f"[LLM Chain #5] Calling Cloudflare Workers AI with model: {model}")
            payload = {"messages": messages}
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    res_obj = data.get("result", {})
                    content = res_obj.get("response", "")
                    if not content and "choices" in res_obj:
                        content = res_obj["choices"][0]["message"]["content"]
                    usage = res_obj.get("usage", {})
                    return LLMResponse(
                        content=content,
                        model=f"cloudflare:{model}",
                        prompt_tokens=usage.get("prompt_tokens", 0),
                        completion_tokens=usage.get("completion_tokens", 0),
                        total_tokens=usage.get("total_tokens", 0)
                    )
        except Exception as e:
            logger.warning(f"Cloudflare attempt failed: {e}")
        return None

    async def _try_pollinations(self, messages: List[Dict[str, str]], temperature: float, max_tokens: Optional[int]) -> Optional[LLMResponse]:
        if not settings.POLLINATIONS_API_KEY:
            return None
        url = "https://text.pollinations.ai/openai/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.POLLINATIONS_API_KEY.strip()}",
            "Content-Type": "application/json"
        }
        try:
            logger.info("[LLM Chain #6] Calling Pollinations AI")
            payload = {
                "model": "openai",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens or 1000
            }
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    return LLMResponse(
                        content=content,
                        model="pollinations:openai",
                        prompt_tokens=usage.get("prompt_tokens", 0),
                        completion_tokens=usage.get("completion_tokens", 0),
                        total_tokens=usage.get("total_tokens", 0)
                    )
        except Exception as e:
            logger.warning(f"Pollinations attempt failed: {e}")
        return None

    async def _try_openai(self, messages: List[Dict[str, str]], temperature: float, max_tokens: Optional[int]) -> Optional[LLMResponse]:
        if not settings.OPENAI_API_KEY:
            return None
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY.strip())
        model = "gpt-4o-mini"
        try:
            logger.info(f"[LLM Chain #7] Calling OpenAI with model: {model}")
            resp = await client.chat.completions.create(
                model=model,
                messages=messages, # type: ignore
                temperature=temperature,
                max_tokens=max_tokens or 1000
            )
            content = resp.choices[0].message.content or ""
            usage = resp.usage
            return LLMResponse(
                content=content,
                model=f"openai:{model}",
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0
            )
        except Exception as e:
            logger.warning(f"OpenAI attempt failed: {e}")
        return None

    def _extractive_fallback(self, messages: List[Dict[str, str]]) -> LLMResponse:
        logger.warning("[LLM Chain Final Fallback] Using local extractive presentation")
        user_content = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_content = m.get("content", "")
                break

        if "RETRIEVED DOCUMENTS" in user_content:
            parts = user_content.split("CURRENT QUESTION")
            docs_part = parts[0].replace("RETRIEVED DOCUMENTS", "").strip()
            question_part = parts[1].strip() if len(parts) > 1 else ""

            content = (
                f"*(Extractive Fallback Response)*\n\n"
                f"**Extracted Context for:** *\"{question_part}\"*\n\n"
                f"{docs_part}"
            )
        else:
            content = "No relevant context could be extracted."

        return LLMResponse(
            content=content,
            model="extractive-fallback",
            prompt_tokens=len(user_content) // 4,
            completion_tokens=len(content) // 4,
            total_tokens=(len(user_content) + len(content)) // 4
        )

    async def generate(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        
        # 1. Ollama Cloud (User's First Choice)
        try:
            resp = await self._try_ollama(messages, temperature, max_tokens)
            if resp:
                return resp
        except Exception as e:
            logger.warning(f"Ollama Cloud attempt error: {e}. Moving to next fallback in chain.")

        # 2. Groq
        try:
            resp = await self._try_groq(messages, temperature, max_tokens)
            if resp:
                return resp
        except Exception as e:
            logger.warning(f"Groq attempt error: {e}. Moving to next fallback in chain.")

        # 3. HuggingFace
        try:
            resp = await self._try_huggingface(messages, temperature, max_tokens)
            if resp:
                return resp
        except Exception as e:
            logger.warning(f"HuggingFace attempt error: {e}. Moving to next fallback in chain.")

        # 4. NVIDIA NIM
        try:
            resp = await self._try_nvidia(messages, temperature, max_tokens)
            if resp:
                return resp
        except Exception as e:
            logger.warning(f"NVIDIA attempt error: {e}. Moving to next fallback in chain.")

        # 5. Cloudflare Workers AI
        try:
            resp = await self._try_cloudflare(messages)
            if resp:
                return resp
        except Exception as e:
            logger.warning(f"Cloudflare attempt error: {e}. Moving to next fallback in chain.")

        # 6. Pollinations AI
        try:
            resp = await self._try_pollinations(messages, temperature, max_tokens)
            if resp:
                return resp
        except Exception as e:
            logger.warning(f"Pollinations attempt error: {e}. Moving to next fallback in chain.")

        # 7. OpenAI
        try:
            resp = await self._try_openai(messages, temperature, max_tokens)
            if resp:
                return resp
        except Exception as e:
            logger.warning(f"OpenAI attempt error: {e}. Moving to next fallback in chain.")

        # 8. Deterministic Extractive Fallback
        return self._extractive_fallback(messages)
