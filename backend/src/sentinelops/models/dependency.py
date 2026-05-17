from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from sentinelops.core.database import Base


class DependencyEdge(Base):
    __tablename__ = "dependency_edges"
    __table_args__ = {'extend_existing': True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    cluster_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    source_namespace: Mapped[str] = mapped_column(String(128))
    source_name: Mapped[str] = mapped_column(String(253))
    source_kind: Mapped[str] = mapped_column(String(64), default="Pod")
    target_namespace: Mapped[str] = mapped_column(String(128))
    target_name: Mapped[str] = mapped_column(String(253))
    target_kind: Mapped[str] = mapped_column(String(64), default="Service")
    edge_type: Mapped[str] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    discovery_method: Mapped[str] = mapped_column(String(64))
    metadata_json: Mapped[str | None] = mapped_column(Text)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class TopologySnapshot(Base):
    __tablename__ = "topology_snapshots"
    __table_args__ = {'extend_existing': True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    cluster_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    graph_json: Mapped[str] = mapped_column(Text, nullable=False)
    node_count: Mapped[int] = mapped_column(default=0)
    edge_count: Mapped[int] = mapped_column(default=0)
    incident_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), index=True)
