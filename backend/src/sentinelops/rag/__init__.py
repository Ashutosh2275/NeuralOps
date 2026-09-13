"""RAG package exports for SentinelOps AI."""
from sentinelops.rag.chunker import DocumentChunk, DocumentMetadata, OperationalDocumentChunker
from sentinelops.rag.context import AssembledContext, Citation, ContextAssembler
from sentinelops.rag.embeddings import (
    BaseEmbeddingProvider,
    DeterministicFallbackEmbeddingProvider,
    EmbeddingResult,
    OllamaEmbeddingProvider,
)
from sentinelops.rag.engine import RAGEngine, get_rag_engine
from sentinelops.rag.vector_store import PersistentVectorStore, ScoredChunk

__all__ = [
    "BaseEmbeddingProvider",
    "OllamaEmbeddingProvider",
    "DeterministicFallbackEmbeddingProvider",
    "EmbeddingResult",
    "DocumentMetadata",
    "DocumentChunk",
    "OperationalDocumentChunker",
    "PersistentVectorStore",
    "ScoredChunk",
    "Citation",
    "AssembledContext",
    "ContextAssembler",
    "RAGEngine",
    "get_rag_engine",
]