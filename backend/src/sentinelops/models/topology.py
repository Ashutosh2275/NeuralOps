from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sentinelops.core.database import Base


class TopologyNode(Base):
    __tablename__ = "topology_nodes"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    cluster_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    topology_version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("topology_versions.id"), index=True)
    node_id: Mapped[str] = mapped_column(String(512), index=True)
    namespace: Mapped[str] = mapped_column(String(128), index=True)
    kind: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(256))
    health: Mapped[str] = mapped_column(String(32), default="unknown")
    labels_json: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class TopologyEdge(Base):
    __tablename__ = "topology_edges"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    cluster_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    topology_version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("topology_versions.id"), index=True)
    source_node_id: Mapped[str] = mapped_column(String(512), index=True)
    target_node_id: Mapped[str] = mapped_column(String(512), index=True)
    edge_type: Mapped[str] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    discovery_method: Mapped[str] = mapped_column(String(64))
    health: Mapped[str] = mapped_column(String(32), default="healthy")
    metadata_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class DependencyScore(Base):
    __tablename__ = "dependency_scores"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    cluster_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    source_node_id: Mapped[str] = mapped_column(String(512), index=True)
    target_node_id: Mapped[str] = mapped_column(String(512), index=True)
    influence_score: Mapped[float] = mapped_column(Float, default=0.5)
    blast_radius: Mapped[int] = mapped_column(Integer, default=0)
    propagation_depth: Mapped[int] = mapped_column(Integer, default=1)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
