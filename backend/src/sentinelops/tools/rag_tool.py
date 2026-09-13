"""
Operational knowledge retrieval tool connecting investigation agents to the Phase 2 RAG engine.
Returns relevant runbook passages, remediation steps, and citations.
"""
from __future__ import annotations

from typing import Any, Optional

from sentinelops.core.logging import get_logger
from sentinelops.rag.engine import RAGEngine, get_rag_engine
from sentinelops.tools.base import BaseTool, PermissionLevel, ToolMetadata, ToolResult

log = get_logger(__name__)


class SearchKnowledgeBaseTool(BaseTool):
    """Retrieves operational knowledge, runbooks, and post-mortems via the RAG engine."""

    def __init__(self, rag_engine: Optional[RAGEngine] = None) -> None:
        super().__init__(
            ToolMetadata(
                name="search_operational_knowledge",
                description="Searches indexed operational runbooks, architecture docs, and post-mortems for diagnosis/remediation advice.",
                parameters={
                    "query": {"type": "string", "description": "Search query or symptoms (e.g. 'CrashLoopBackOff payment-service')"},
                    "top_k": {"type": "integer", "description": "Number of knowledge chunks to return (default: 3)"},
                    "category": {"type": "string", "description": "Optional category filter: runbook, postmortem, architecture"},
                },
                required_params=["query"],
                category="rag",
                permission=PermissionLevel.READ_ONLY,
                timeout_seconds=6.0,
            )
        )
        self._rag = rag_engine

    def _get_engine(self) -> RAGEngine:
        if self._rag is None:
            self._rag = get_rag_engine()
        return self._rag

    async def run(self, **kwargs: Any) -> ToolResult:
        query = str(kwargs.get("query", "")).strip()
        top_k = min(int(kwargs.get("top_k", 3)), 10)
        category = kwargs.get("category")

        try:
            engine = self._get_engine()
            filter_meta = {"category": category} if category else None
            assembled = await engine.retrieve_context(
                query=query,
                top_k=top_k,
                filter_metadata=filter_meta,
            )

            citations_data = [
                {
                    "title": c.title,
                    "section": c.section,
                    "relevance_score": round(c.relevance_score, 3),
                    "chunk_id": c.chunk_id,
                }
                for c in assembled.citations
            ]

            return ToolResult(
                tool_name=self.name,
                success=True,
                data={
                    "query": query,
                    "has_knowledge": assembled.has_relevant_knowledge,
                    "context_text": assembled.context_text,
                    "citations": citations_data,
                    "chunk_count": len(assembled.citations),
                },
                source="rag_engine",
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data=None,
                errors=[f"Knowledge retrieval failed: {str(e)}"],
                source="rag_engine",
            )
