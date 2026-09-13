"""
RAG Engine facade for SentinelOps AI.
Coordinates ingestion, vector storage, retrieval, context assembly, and knowledge querying.
Singleton instance initialized on demand.
"""
from __future__ import annotations

import os
from typing import Any

from sentinelops.config import get_settings
from sentinelops.core.logging import get_logger
from sentinelops.rag.chunker import DocumentMetadata, OperationalDocumentChunker
from sentinelops.rag.context import AssembledContext, ContextAssembler
from sentinelops.rag.embeddings import (
    BaseEmbeddingProvider,
    DeterministicFallbackEmbeddingProvider,
    OllamaEmbeddingProvider,
)
from sentinelops.rag.seed_data import SEED_DOCUMENTS
from sentinelops.rag.vector_store import PersistentVectorStore, ScoredChunk

log = get_logger(__name__)


class RAGEngine:
    """Enterprise RAG subsystem for SentinelOps AI."""

    def __init__(
        self,
        vector_store: PersistentVectorStore | None = None,
        embedding_provider: BaseEmbeddingProvider | None = None,
        chunker: OperationalDocumentChunker | None = None,
        assembler: ContextAssembler | None = None,
    ) -> None:
        settings = get_settings()
        self.embedding_provider = embedding_provider or OllamaEmbeddingProvider()
        self.chunker = chunker or OperationalDocumentChunker()
        self.assembler = assembler or ContextAssembler(
            max_context_chars=settings.rag_max_context_tokens * 4,
            max_chunks=settings.rag_default_top_k,
            min_relevance=settings.rag_min_relevance_score,
        )

        storage_path = os.path.join(settings.rag_storage_dir, "vectors.db")
        self.vector_store = vector_store or PersistentVectorStore(
            storage_path=storage_path,
            embedding_provider=self.embedding_provider,
        )

    async def ingest_document(
        self,
        content: str,
        metadata: DocumentMetadata,
    ) -> int:
        """Chunks and indexes an operational document."""
        chunks = self.chunker.chunk_document(content, metadata)
        if not chunks:
            return 0
        return await self.vector_store.upsert_chunks(chunks, self.embedding_provider)

    async def seed_knowledge_base(self) -> int:
        """Seed pre-packaged operational runbooks and post-mortems if store is empty or needs refresh."""
        total_indexed = 0
        for meta, content in SEED_DOCUMENTS:
            indexed = await self.ingest_document(content, meta)
            total_indexed += indexed
        log.info("rag_knowledge_base_seeded", total_new_indexed=total_indexed, store_total=self.vector_store.count())
        return total_indexed

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        min_score: float | None = None,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[ScoredChunk]:
        """Performs semantic similarity search over stored operational knowledge."""
        settings = get_settings()
        k = top_k or settings.rag_default_top_k
        thresh = min_score if min_score is not None else settings.rag_min_relevance_score

        return await self.vector_store.search(
            query=query,
            top_k=k,
            min_score=thresh,
            filter_metadata=filter_metadata,
            embedding_provider=self.embedding_provider,
        )

    async def retrieve_context(
        self,
        query: str,
        top_k: int | None = None,
        min_score: float | None = None,
        filter_metadata: dict[str, Any] | None = None,
    ) -> AssembledContext:
        """Retrieves and assembles context with citations and deduplication."""
        scored_chunks = await self.retrieve(
            query=query,
            top_k=top_k,
            min_score=min_score,
            filter_metadata=filter_metadata,
        )
        return self.assembler.assemble(scored_chunks)


_rag_engine_instance: RAGEngine | None = None


def get_rag_engine() -> RAGEngine:
    global _rag_engine_instance
    if _rag_engine_instance is None:
        _rag_engine_instance = RAGEngine()
    return _rag_engine_instance