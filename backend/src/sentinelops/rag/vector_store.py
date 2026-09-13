"""
Persistent Vector Store for SentinelOps AI RAG knowledge system.
Features:
- Thread-safe, SQLite-backed persistence storing vectors, text chunks, and JSON metadata.
- Optimized vector cosine-similarity search using NumPy vectorized matrix math.
- Exact metadata filtering across services, namespaces, environments, and document types.
- Content-addressable hashing to prevent redundant re-indexing.
- Zero-external-dependency persistence resilient across application restarts.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from dataclasses import dataclass
from typing import Any

import numpy as np

from sentinelops.core.logging import get_logger
from sentinelops.rag.chunker import DocumentChunk
from sentinelops.rag.embeddings import BaseEmbeddingProvider, EmbeddingResult

log = get_logger(__name__)


@dataclass
class ScoredChunk:
    chunk_id: str
    document_id: str
    title: str
    section: str
    content: str
    score: float
    metadata: dict[str, Any]
    provider_type: str


class PersistentVectorStore:
    """
    Production-grade persistent vector database.
    Stores chunks and embedding vectors in SQLite with fast in-memory matrix caching for similarity queries.
    """

    def __init__(
        self,
        storage_path: str = "data/rag_store/vectors.db",
        embedding_provider: BaseEmbeddingProvider | None = None,
    ) -> None:
        self.storage_path = storage_path
        self._embedding_provider = embedding_provider
        self._lock = threading.RLock()
        self._conn: sqlite3.Connection | None = None

        # In-memory vector matrix cache for fast retrieval
        self._chunk_ids: list[str] = []
        self._matrix: np.ndarray | None = None
        self._records: dict[str, dict[str, Any]] = {}

        self._init_db()
        self._load_cache()

    def _init_db(self) -> None:
        os.makedirs(os.path.dirname(self.storage_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(self.storage_path, check_same_thread=False)
        with self._lock, self._conn:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS vector_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    section TEXT NOT NULL,
                    content TEXT NOT NULL,
                    order_index INTEGER NOT NULL,
                    metadata_json TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    provider_type TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    dimension INTEGER NOT NULL,
                    vector_blob BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            self._conn.execute("CREATE INDEX IF NOT EXISTS ix_doc_id ON vector_chunks(document_id);")
            self._conn.execute("CREATE INDEX IF NOT EXISTS ix_content_hash ON vector_chunks(content_hash);")

    def _load_cache(self, target_dim: int | None = None) -> None:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("""
                SELECT chunk_id, document_id, title, section, content, metadata_json,
                       provider_type, dimension, vector_blob
                FROM vector_chunks
            """)
            rows = cursor.fetchall()
            self._chunk_ids = []
            vectors: list[np.ndarray] = []
            self._records = {}

            if not rows:
                self._matrix = None
                return

            chosen_dim = target_dim
            if chosen_dim is None and self._embedding_provider:
                chosen_dim = getattr(self._embedding_provider, "dimension", None)
            if chosen_dim is None:
                chosen_dim = rows[-1][7]

            for r in rows:
                cid, doc_id, title, sec, text, meta_json, p_type, dim, blob = r
                if chosen_dim is not None and dim != chosen_dim:
                    continue
                vec = np.frombuffer(blob, dtype=np.float32)
                if vec.shape[0] == dim:
                    self._chunk_ids.append(cid)
                    vectors.append(vec)
                    self._records[cid] = {
                        "chunk_id": cid,
                        "document_id": doc_id,
                        "title": title,
                        "section": sec,
                        "content": text,
                        "metadata": json.loads(meta_json),
                        "provider_type": p_type,
                        "dimension": dim,
                    }

            if vectors:
                self._matrix = np.vstack(vectors)
            else:
                self._matrix = None

    def count(self) -> int:
        with self._lock:
            return len(self._chunk_ids)

    async def upsert_chunks(
        self,
        chunks: list[DocumentChunk],
        embedding_provider: BaseEmbeddingProvider | None = None,
    ) -> int:
        provider = embedding_provider or self._embedding_provider
        if not provider:
            raise ValueError("No embedding provider configured for vector store upsert.")

        new_or_changed = []
        with self._lock:
            cursor = self._conn.cursor()
            for ch in chunks:
                cursor.execute(
                    "SELECT content_hash FROM vector_chunks WHERE chunk_id = ?",
                    (ch.chunk_id,),
                )
                row = cursor.fetchone()
                if not row or row[0] != ch.content_hash:
                    new_or_changed.append(ch)

        if not new_or_changed:
            return 0

        # Generate embeddings in batch
        texts = [c.content for c in new_or_changed]
        embeddings: list[EmbeddingResult] = await provider.embed_batch(texts)

        with self._lock, self._conn:
            for ch, emb in zip(new_or_changed, embeddings):
                vec_arr = np.array(emb.vector, dtype=np.float32)
                # Normalize vector to unit length for fast cosine dot product
                norm = np.linalg.norm(vec_arr)
                if norm > 0:
                    vec_arr = vec_arr / norm

                blob = vec_arr.tobytes()
                self._conn.execute("""
                    INSERT OR REPLACE INTO vector_chunks (
                        chunk_id, document_id, title, section, content, order_index,
                        metadata_json, content_hash, provider_type, model_name,
                        dimension, vector_blob
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ch.chunk_id,
                    ch.document_id,
                    ch.title,
                    ch.section,
                    ch.content,
                    ch.order_index,
                    json.dumps(ch.metadata),
                    ch.content_hash,
                    emb.provider_type,
                    emb.model_name,
                    emb.dimension,
                    blob,
                ))

        self._load_cache()
        log.info("vector_store_upsert_complete", indexed_count=len(new_or_changed))
        return len(new_or_changed)

    async def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.2,
        filter_metadata: dict[str, Any] | None = None,
        embedding_provider: BaseEmbeddingProvider | None = None,
    ) -> list[ScoredChunk]:
        provider = embedding_provider or self._embedding_provider
        if not provider:
            raise ValueError("No embedding provider configured for vector store query.")

        query_emb = await provider.embed_text(query)
        q_vec = np.array(query_emb.vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        with self._lock:
            if self._matrix is None or self._matrix.shape[1] != q_vec.shape[0]:
                self._load_cache(target_dim=q_vec.shape[0])

            if self._matrix is None or len(self._chunk_ids) == 0:
                return []

            # Cosine similarity via dot product of normalized vectors
            scores = np.dot(self._matrix, q_vec)
            top_indices = np.argsort(scores)[::-1]

            results: list[ScoredChunk] = []
            for idx in top_indices:
                score = float(scores[idx])
                if score < min_score:
                    continue

                cid = self._chunk_ids[idx]
                record = self._records[cid]

                # Metadata filtering
                if filter_metadata:
                    meta = record["metadata"]
                    matches = True
                    for k, expected in filter_metadata.items():
                        actual = meta.get(k)
                        if isinstance(expected, list):
                            if actual not in expected:
                                matches = False
                                break
                        elif actual != expected:
                            matches = False
                            break
                    if not matches:
                        continue

                results.append(
                    ScoredChunk(
                        chunk_id=record["chunk_id"],
                        document_id=record["document_id"],
                        title=record["title"],
                        section=record["section"],
                        content=record["content"],
                        score=round(score, 4),
                        metadata=record["metadata"],
                        provider_type=record["provider_type"],
                    )
                )

                if len(results) >= top_k:
                    break

            return results

    def delete_document(self, document_id: str) -> int:
        with self._lock, self._conn:
            cursor = self._conn.execute(
                "DELETE FROM vector_chunks WHERE document_id = ?",
                (document_id,),
            )
            deleted = cursor.rowcount
            self._load_cache()
            return deleted

    def clear(self) -> None:
        with self._lock, self._conn:
            self._conn.execute("DELETE FROM vector_chunks")
            self._load_cache()


VectorStore = PersistentVectorStore
_default_vector_store: Optional[PersistentVectorStore] = None


def get_vector_store(db_path: str = "data/rag_store/vectors.db") -> PersistentVectorStore:
    global _default_vector_store
    if _default_vector_store is None:
        _default_vector_store = PersistentVectorStore(storage_path=db_path)
    return _default_vector_store