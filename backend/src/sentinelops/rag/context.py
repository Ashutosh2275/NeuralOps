"""
Context assembly, relevance filtering, and source citation engine for SentinelOps AI RAG.
Features:
- Ranks retrieved chunks by relevance score and provenance.
- De-duplicates overlapping section chunks.
- Enforces strict token/character context windows to prevent prompt bloat.
- Formats verifiable Markdown citations mapping back to real knowledge documents.
- Sanitizes retrieved chunks against prompt injection.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from sentinelops.rag.vector_store import ScoredChunk


@dataclass
class Citation:
    source_id: str
    title: str
    section: str
    document_type: str
    service: str | None
    relevance_score: float
    excerpt: str

    @property
    def chunk_id(self) -> str:
        return self.source_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "title": self.title,
            "section": self.section,
            "document_type": self.document_type,
            "service": self.service,
            "relevance_score": self.relevance_score,
            "excerpt": self.excerpt,
        }


@dataclass
class AssembledContext:
    context_text: str
    citations: list[Citation]
    total_chunks: int
    used_chunks: int
    has_relevant_knowledge: bool
    provider_types: list[str] = field(default_factory=list)


class PromptSanitizer:
    """Sanitizes untrusted operational documents against prompt injection attacks."""

    INJECTION_PATTERNS = [
        re.compile(r"ignore (all )?previous instructions", re.I),
        re.compile(r"system prompt:", re.I),
        re.compile(r"you are now (a|an)", re.I),
        re.compile(r"bypass safety", re.I),
        re.compile(r"print all environment variables", re.I),
        re.compile(r"expose all secrets", re.I),
        re.compile(r"sudo rm -rf", re.I),
    ]

    SECRET_PATTERNS = [
        (re.compile(r"Bearer\s+eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9._-]+", re.I), "[TOKEN_REDACTED]"),
        (re.compile(r"AKIA[0-9A-Z]{16}", re.I), "[AWS_KEY_REDACTED]"),
        (re.compile(r"AWS_SECRET_KEY=[A-Za-z0-9/+=]{16,}", re.I), "[SECRET_REDACTED]"),
        (re.compile(r"(password|secret|token)\s*=\s*['\"][^'\"]+['\"]", re.I), "[SECRET_REDACTED]"),
    ]

    @classmethod
    def sanitize(cls, text: str) -> str:
        sanitized = text
        for pattern in cls.INJECTION_PATTERNS:
            sanitized = pattern.sub("[REDACTED_SUSPICIOUS_INSTRUCTION]", sanitized)
        for pattern, repl in cls.SECRET_PATTERNS:
            sanitized = pattern.sub(repl, sanitized)
        return sanitized


class ContextAssembler:
    """Assembles ground-truth evidence and citations for LLM prompting."""

    def __init__(
        self,
        max_context_chars: int = 6000,
        max_chunks: int = 4,
        min_relevance: float = 0.20,
    ) -> None:
        self.max_context_chars = max_context_chars
        self.max_chunks = max_chunks
        self.min_relevance = min_relevance

    def assemble(self, scored_chunks: list[ScoredChunk]) -> AssembledContext:
        if not scored_chunks:
            return AssembledContext(
                context_text="[No operational runbooks or historical post-mortems matched this query.]",
                citations=[],
                total_chunks=0,
                used_chunks=0,
                has_relevant_knowledge=False,
                provider_types=[],
            )

        # Filter by minimum relevance threshold
        filtered = [c for c in scored_chunks if c.score >= self.min_relevance]
        if not filtered:
            return AssembledContext(
                context_text="[No operational documents met the confidence threshold for this query.]",
                citations=[],
                total_chunks=len(scored_chunks),
                used_chunks=0,
                has_relevant_knowledge=False,
                provider_types=[],
            )

        # Deduplicate content
        seen_hashes = set()
        unique_chunks: list[ScoredChunk] = []
        for c in filtered:
            h = f"{c.document_id}:{c.section}"
            if h not in seen_hashes:
                seen_hashes.add(h)
                unique_chunks.append(c)

        # Assemble context blocks within window
        blocks: list[str] = []
        citations: list[Citation] = []
        current_len = 0
        used_count = 0
        providers = set()

        for idx, c in enumerate(unique_chunks[: self.max_chunks], start=1):
            sanitized_content = PromptSanitizer.sanitize(c.content)
            block = (
                f"--- Evidence Source [{idx}]: {c.title} (Section: {c.section}, Relevance: {c.score:.2f}) ---\n"
                f"{sanitized_content}\n"
            )

            if current_len + len(block) > self.max_context_chars and blocks:
                break

            blocks.append(block)
            current_len += len(block)
            used_count += 1
            providers.add(c.provider_type)

            # Generate formal verifiable citation
            excerpt = sanitized_content[:200].replace("\n", " ") + "..."
            citations.append(
                Citation(
                    source_id=c.document_id,
                    title=c.title,
                    section=c.section,
                    document_type=c.metadata.get("document_type", "operational_doc"),
                    service=c.metadata.get("service") or None,
                    relevance_score=c.score,
                    excerpt=excerpt,
                )
            )

        assembled_text = "\n".join(blocks).strip()

        return AssembledContext(
            context_text=assembled_text,
            citations=citations,
            total_chunks=len(scored_chunks),
            used_chunks=used_count,
            has_relevant_knowledge=True,
            provider_types=sorted(providers),
        )