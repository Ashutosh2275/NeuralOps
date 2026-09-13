"""
Knowledge & Operational RAG API endpoints for SentinelOps AI.
Exposes indexed operational runbooks, architecture specs, post-mortems, and semantic search.
"""
from __future__ import annotations

import sqlite3
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from sentinelops.rag.engine import RAGEngine
from sentinelops.rag.vector_store import get_vector_store

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class SearchKnowledgeRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Semantic operational query")
    top_k: int = Field(4, ge=1, le=10, description="Max documents to retrieve")


@router.get("/documents", summary="List all indexed operational runbooks and knowledge artifacts")
async def list_documents() -> dict[str, Any]:
    """Retrieve distinct documents and metadata from the persistent vector store."""
    try:
        store = get_vector_store()
        db_path = getattr(store, "storage_path", "data/rag_store/vectors.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("""
            SELECT document_id, title, provider_type, COUNT(chunk_id) as chunk_count
            FROM vector_chunks
            GROUP BY document_id, title, provider_type
            ORDER BY document_id ASC
        """)
        rows = c.fetchall()
        conn.close()

        docs = [
            {
                "document_id": r[0],
                "title": r[1],
                "provider_type": r[2],
                "chunk_count": r[3],
                "status": "indexed",
            }
            for r in rows
        ]
        return {
            "count": len(docs),
            "total_chunks": sum(d["chunk_count"] for d in docs),
            "documents": docs,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read knowledge store: {str(e)}")


@router.post("/search", summary="Perform real semantic vector search against operational corpus")
async def search_knowledge(req: SearchKnowledgeRequest) -> dict[str, Any]:
    """Execute cosine similarity search using Ollama nomic-embed-text."""
    try:
        rag = RAGEngine()
        results = await rag.retrieve(query=req.query, top_k=req.top_k)
        items = [
            {
                "chunk_id": r.chunk_id,
                "document_id": r.document_id,
                "title": r.title,
                "section": r.section,
                "content": r.content,
                "score": round(r.score, 4),
                "metadata": r.metadata,
            }
            for r in results
        ]
        return {
            "query": req.query,
            "count": len(items),
            "results": items,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic retrieval failed: {str(e)}")


@router.get("/documents/{document_id}", summary="Retrieve full document details, content and sections")
async def get_document(document_id: str) -> dict[str, Any]:
    try:
        store = get_vector_store()
        db_path = getattr(store, "storage_path", "data/rag_store/vectors.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("""
            SELECT chunk_id, title, provider_type, section, content, metadata_json
            FROM vector_chunks
            WHERE document_id = ?
            ORDER BY order_index ASC
        """, (document_id,))
        rows = c.fetchall()
        conn.close()

        if not rows:
            raise HTTPException(status_code=404, detail=f"Knowledge document '{document_id}' not found")

        chunks = []
        for r in rows:
            meta = {}
            if r[5]:
                try:
                    import json
                    meta = json.loads(r[5])
                except Exception:
                    pass
            chunks.append({
                "chunk_id": r[0],
                "title": r[1],
                "provider_type": r[2],
                "section": r[3],
                "content": r[4],
                "metadata": meta,
            })

        full_content = "\n\n".join(c["content"] for c in chunks)

        return {
            "document_id": document_id,
            "title": rows[0][1],
            "provider_type": rows[0][2],
            "chunk_count": len(chunks),
            "full_content": full_content,
            "chunks": chunks,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch document: {str(e)}")

