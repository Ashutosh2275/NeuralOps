"""
Embedding provider abstraction for SentinelOps AI.
Generates genuine numerical embedding vectors via Ollama with an isolated deterministic fallback.
Explicitly identifies whether vectors originated from REAL EMBEDDING or FALLBACK.
"""
from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod
from typing import Literal

import httpx
import numpy as np

from sentinelops.config import get_settings
from sentinelops.core.logging import get_logger

log = get_logger(__name__)

ProviderType = Literal["REAL_EMBEDDING", "FALLBACK"]


class EmbeddingResult:
    """Wrapper holding embedding vector and provenance metadata."""

    def __init__(
        self,
        vector: list[float],
        dimension: int,
        provider_type: ProviderType,
        model_name: str,
    ) -> None:
        self.vector = vector
        self.dimension = dimension
        self.provider_type: ProviderType = provider_type
        self.model_name = model_name

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension,
            "provider_type": self.provider_type,
            "model_name": self.model_name,
            "sample": self.vector[:5] if len(self.vector) >= 5 else self.vector,
        }


class BaseEmbeddingProvider(ABC):
    """Abstract interface for embedding generators."""

    @abstractmethod
    async def embed_text(self, text: str) -> EmbeddingResult:
        """Embed a single query or text document."""
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Embed a batch of texts."""
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        ...


class DeterministicFallbackEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic pseudo-semantic embedding using multi-gram hashing and tf-idf hashing.
    Used exclusively as a safe offline fallback.
    Never represented as a real semantic model.
    """

    def __init__(self, dimension: int = 384) -> None:
        self._dimension = dimension
        self._model_name = "deterministic-hash-384"

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def _hash_token(self, token: str) -> tuple[int, float]:
        """Maps a token to an index and sign weight using SHA-256."""
        h = hashlib.sha256(token.encode("utf-8")).digest()
        idx = int.from_bytes(h[:4], "big") % self._dimension
        sign = 1.0 if h[4] % 2 == 0 else -1.0
        return idx, sign

    def _generate_vector(self, text: str) -> list[float]:
        vec = np.zeros(self._dimension, dtype=np.float32)
        tokens = re.findall(r"\w+", text.lower())
        if not tokens:
            return vec.tolist()

        # Stopwords to filter for clean sparse-dense semantic representation
        stopwords = {
            "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or", "is",
            "are", "was", "were", "be", "been", "being", "have", "has", "had", "do",
            "does", "did", "how", "what", "which", "why", "can", "could", "should",
            "would", "i", "me", "my", "we", "our", "you", "your", "it", "its", "if",
        }

        # Token frequencies & bigrams
        counts: dict[str, float] = {}
        content_tokens = [t for t in tokens if t not in stopwords and len(t) > 1]
        for t in content_tokens:
            # Boost domain keywords
            weight = 2.5 if len(t) > 4 else 1.0
            counts[t] = counts.get(t, 0.0) + weight

        for i in range(len(content_tokens) - 1):
            bg = f"{content_tokens[i]}_{content_tokens[i+1]}"
            counts[bg] = counts.get(bg, 0.0) + 2.0

        for term, weight in counts.items():
            idx, sign = self._hash_token(term)
            vec[idx] += weight * sign

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    async def embed_text(self, text: str) -> EmbeddingResult:
        vec = self._generate_vector(text)
        return EmbeddingResult(
            vector=vec,
            dimension=self._dimension,
            provider_type="FALLBACK",
            model_name=self._model_name,
        )

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        return [await self.embed_text(t) for t in texts]


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """
    Real Embedding Provider querying Ollama's /api/embeddings or /api/embed endpoints.
    Produces authentic deep learning neural vectors.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self._model = model or getattr(settings, "ollama_embedding_model", None) or "nomic-embed-text"
        self._timeout = timeout_seconds
        self._fallback = DeterministicFallbackEmbeddingProvider()
        self._dimension_detected: int | None = None

    @property
    def dimension(self) -> int:
        return self._dimension_detected or 384

    @property
    def model_name(self) -> str:
        return self._model

    async def embed_text(self, text: str) -> EmbeddingResult:
        if not text.strip():
            return await self._fallback.embed_text(text)

        # Primary: Ollama /api/embeddings
        url = f"{self._base_url}/api/embeddings"
        payload = {"model": self._model, "prompt": text}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    embedding = data.get("embedding")
                    if isinstance(embedding, list) and len(embedding) > 0:
                        self._dimension_detected = len(embedding)
                        return EmbeddingResult(
                            vector=[float(x) for x in embedding],
                            dimension=len(embedding),
                            provider_type="REAL_EMBEDDING",
                            model_name=self._model,
                        )
                
                # Alternate /api/embed endpoint (newer Ollama versions)
                url_embed = f"{self._base_url}/api/embed"
                resp_embed = await client.post(url_embed, json={"model": self._model, "input": text})
                if resp_embed.status_code == 200:
                    data_embed = resp_embed.json()
                    embeddings = data_embed.get("embeddings")
                    if isinstance(embeddings, list) and len(embeddings) > 0:
                        vec = embeddings[0]
                        self._dimension_detected = len(vec)
                        return EmbeddingResult(
                            vector=[float(x) for x in vec],
                            dimension=len(vec),
                            provider_type="REAL_EMBEDDING",
                            model_name=self._model,
                        )

                log.warning(
                    "ollama_embedding_failed_status",
                    status=resp.status_code,
                    body=resp.text[:200],
                )
        except Exception as e:
            log.warning("ollama_embedding_unreachable", error=str(e), model=self._model)

        # Graceful fallback with clear provenance tag
        return await self._fallback.embed_text(text)

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        results: list[EmbeddingResult] = []
        for text in texts:
            res = await self.embed_text(text)
            results.append(res)
        return results