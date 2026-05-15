import json
from collections.abc import AsyncIterator

import httpx

from sentinelops.config import get_settings
from sentinelops.core.logging import get_logger

log = get_logger(__name__)


class OllamaClient:
    def __init__(self) -> None:
        self._settings = get_settings()

    async def generate(self, prompt: str, model: str | None = None, system: str | None = None) -> str:
        model = model or self._settings.ollama_model
        url = f"{self._settings.ollama_base_url}/api/generate"
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "num_predict": self._settings.ollama_max_tokens,
                "num_ctx": 4096,
                "temperature": 0.3,
            },
        }
        try:
            async with httpx.AsyncClient(timeout=self._settings.ollama_timeout_seconds) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                return resp.json().get("response", "")
        except Exception as e:
            log.warning("ollama_generate_failed", model=model, error=str(e))
            if model != self._settings.ollama_fallback_model:
                return await self.generate(prompt, self._settings.ollama_fallback_model, system)
            return f"[AI unavailable] {e}"

    async def generate_stream(self, prompt: str, model: str | None = None) -> AsyncIterator[str]:
        model = model or self._settings.ollama_model
        url = f"{self._settings.ollama_base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {"num_predict": self._settings.ollama_max_tokens, "num_ctx": 4096},
        }
        async with httpx.AsyncClient(timeout=self._settings.ollama_timeout_seconds) as client:
            async with client.stream("POST", url, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        if token := chunk.get("response"):
                            yield token
                    except json.JSONDecodeError:
                        continue

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self._settings.ollama_base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False
