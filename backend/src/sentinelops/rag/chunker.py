"""
Document chunker and cleaner for SentinelOps AI operational documents.
Splits Markdown/TXT operational runbooks, post-mortems, and architecture specs
into structured chunks while preserving hierarchy, metadata, and technical commands.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass
class DocumentMetadata:
    document_id: str
    title: str
    source: str
    document_type: str  # runbook | postmortem | architecture | procedure
    service: str | None = None
    namespace: str | None = None
    environment: str = "production"
    version: str = "1.0"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: list[str] = field(default_factory=list)
    custom_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "title": self.title,
            "source": self.source,
            "document_type": self.document_type,
            "service": self.service or "",
            "namespace": self.namespace or "",
            "environment": self.environment,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tags": self.tags,
            **self.custom_metadata,
        }


@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    title: str
    section: str
    content: str
    order_index: int
    metadata: dict[str, Any]
    content_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "title": self.title,
            "section": self.section,
            "content": self.content,
            "order_index": self.order_index,
            "metadata": self.metadata,
            "content_hash": self.content_hash,
        }


class DocumentCleaner:
    """Cleans and sanitizes operational documents prior to chunking."""

    @staticmethod
    def clean(raw_text: str) -> str:
        if not raw_text:
            return ""

        # Normalize carriage returns
        text = raw_text.replace("\r\n", "\n").replace("\r", "\n")

        # Strip null bytes and non-printable control characters (except newline, tab)
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

        # Remove HTML comments
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

        # Collapse excess empty lines (max 2 consecutive)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Collapse multiple spaces and trim lines
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
        return "\n".join(lines).strip()


class OperationalDocumentChunker:
    """
    Hierarchical markdown/text chunker tailored for Kubernetes runbooks and SRE documents.
    Preserves:
    - Code blocks and kubectl commands intact.
    - Header hierarchy as section breadcrumbs.
    - Configurable chunk size (target: ~400-800 tokens, 1500-2500 chars) with semantic overlap.
    """

    def __init__(
        self,
        target_chunk_size: int = 1800,
        chunk_overlap: int = 250,
        min_chunk_size: int = 200,
    ) -> None:
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def chunk_document(
        self,
        content: str,
        metadata: DocumentMetadata,
    ) -> list[DocumentChunk]:
        cleaned = DocumentCleaner.clean(content)
        if not cleaned:
            return []

        # Split along markdown headers (H1, H2, H3)
        header_pattern = re.compile(r"^(#{1,3}\s+.+)$", re.MULTILINE)
        splits = header_pattern.split(cleaned)

        sections: list[tuple[str, str]] = []
        current_header = metadata.title or "General Overview"

        i = 0
        while i < len(splits):
            part = splits[i].strip()
            if not part:
                i += 1
                continue

            if part.startswith("#"):
                current_header = re.sub(r"^#+\s*", "", part)
                content_part = splits[i + 1].strip() if i + 1 < len(splits) else ""
                sections.append((current_header, content_part))
                i += 2
            else:
                sections.append((current_header, part))
                i += 1

        chunks: list[DocumentChunk] = []
        order = 0

        for section_title, section_body in sections:
            if not section_body:
                continue

            # Sub-chunk section if larger than target_chunk_size
            sub_chunks = self._split_section_with_overlap(section_body)
            for sub_text in sub_chunks:
                if len(sub_text.strip()) < self.min_chunk_size and len(sub_chunks) > 1:
                    continue

                chunk_content = f"[{metadata.title} > {section_title}]\n{sub_text.strip()}"
                content_hash = hashlib.sha256(chunk_content.encode("utf-8")).hexdigest()
                chunk_id = hashlib.md5(
                    f"{metadata.document_id}:{order}:{content_hash[:8]}".encode()
                ).hexdigest()

                chunk_meta = metadata.to_dict()
                chunk_meta["section"] = section_title
                chunk_meta["order_index"] = order

                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=metadata.document_id,
                        title=metadata.title,
                        section=section_title,
                        content=chunk_content,
                        order_index=order,
                        metadata=chunk_meta,
                        content_hash=content_hash,
                    )
                )
                order += 1

        return chunks

    def _split_section_with_overlap(self, text: str) -> list[str]:
        if len(text) <= self.target_chunk_size:
            return [text]

        paragraphs = text.split("\n\n")
        chunks: list[str] = []
        current_chunk: list[str] = []
        current_len = 0

        for p in paragraphs:
            p_clean = p.strip()
            if not p_clean:
                continue

            if current_len + len(p_clean) > self.target_chunk_size and current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                chunks.append(chunk_text)

                # Overlap logic: retain last paragraph if small enough
                if len(current_chunk[-1]) <= self.chunk_overlap:
                    current_chunk = [current_chunk[-1], p_clean]
                    current_len = len(current_chunk[0]) + len(p_clean)
                else:
                    current_chunk = [p_clean]
                    current_len = len(p_clean)
            else:
                current_chunk.append(p_clean)
                current_len += len(p_clean)

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks