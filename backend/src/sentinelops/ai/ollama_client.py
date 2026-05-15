import asyncio
import json
import time
from typing import Optional

import httpx

from sentinelops.config import get_settings
from sentinelops.core.logging import get_logger

log = get_logger(__name__)

SUPPORTED_MODELS = {
    "llama3.2": {"context": 8192, "tokens_max": 2048},
    "mistral": {"context": 8192, "tokens_max": 2048},
    "phi3": {"context": 4096, "tokens_max": 1024},
    "qwen2.5": {"context": 8192, "tokens_max": 2048},
}


class OllamaClient:
    """Enhanced Ollama client with model management, failover, and safety."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._primary_model = self._settings.ollama_model
        self._fallback_models = [self._settings.ollama_fallback_model]
        self._model_cache: dict[str, bool] = {}
        self._timeout = self._settings.ollama_timeout_seconds

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> tuple[str, dict]:
        """Generate with fallback, returning (response, metadata)."""
        model = model or self._primary_model
        max_tokens = max_tokens or self._settings.ollama_max_tokens

        # Truncate prompt if too long
        max_context = SUPPORTED_MODELS.get(model, {}).get("context", 4096)
        if len(prompt) > max_context * 4:
            prompt = prompt[-max_context * 4 :]

        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                start = time.time()
                resp = await client.post(
                    f"{self._settings.ollama_base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "num_predict": min(max_tokens, 2048),
                            "num_ctx": max_context,
                            "temperature": temperature,
                        },
                    },
                )
                latency_ms = int((time.time() - start) * 1000)
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", ""), {
                    "model": model,
                    "tokens": data.get("eval_count", 0),
                    "latency_ms": latency_ms,
                    "success": True,
                }
        except Exception as e:
            log.warning("ollama_generation_failed", model=model, error=str(e))
            if model != self._fallback_models[0]:
                log.info("fallback_to_model", model=self._fallback_models[0])
                return await self.generate(
                    prompt, system, self._fallback_models[0], temperature, max_tokens
                )
            return f"[Inference unavailable: {str(e)[:100]}]", {
                "model": model,
                "success": False,
                "error": str(e),
            }

    async def health_check(self) -> bool:
        """Check Ollama service availability."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self._settings.ollama_base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    async def pull_model(self, model: str) -> bool:
        """Pull a model from registry."""
        try:
            async with httpx.AsyncClient(timeout=300) as client:
                resp = await client.post(
                    f"{self._settings.ollama_base_url}/api/pull",
                    json={"name": model},
                )
                resp.raise_for_status()
                self._model_cache[model] = True
                return True
        except Exception as e:
            log.warning("model_pull_failed", model=model, error=str(e))
            return False

    async def validate_response(self, response: str, expected_services: list[str]) -> tuple[bool, str]:
        """Validate response doesn't hallucinate services."""
        response_lower = response.lower()
        hallucinated = []

        for svc in expected_services:
            if svc.lower() in response_lower:
                continue
            if f"'{svc}'" in response or f'"{svc}"' in response:
                continue
            hallucinated.append(svc)

        if hallucinated:
            return False, f"May reference non-existent services: {hallucinated}"
        return True, ""
