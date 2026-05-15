from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from sentinelops.core.database import Base


class TopologyVersion(Base):
    __tablename__ = "topology_versions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    cluster_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    snapshot_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), index=True)
    graph_json: Mapped[str] = mapped_column(Text, nullable=False)
    diff_json: Mapped[str | None] = mapped_column(Text)
    node_count: Mapped[int] = mapped_column(Integer, default=0)
    edge_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class CorrelationGroup(Base):
    __tablename__ = "correlation_groups"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), index=True)
    cluster_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    namespace: Mapped[str] = mapped_column(String(128))
    trigger: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(32))
    event_count: Mapped[int] = mapped_column(Integer, default=0)
    related_event_ids_json: Mapped[str | None] = mapped_column(Text)
    dependency_context_json: Mapped[str | None] = mapped_column(Text)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class AIInsight(Base):
    __tablename__ = "ai_insights"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("incidents.id"), index=True)
    agent_type: Mapped[str] = mapped_column(String(64), index=True)
    insight_type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(512))
    content: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.7)
    reasoning: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ReplayFrame(Base):
    __tablename__ = "replay_frames"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("incidents.id"), index=True)
    frame_index: Mapped[int] = mapped_column(Integer)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    event_count: Mapped[int] = mapped_column(Integer, default=0)
    topology_state_json: Mapped[str | None] = mapped_column(Text)
    events_json: Mapped[str | None] = mapped_column(Text)


class ReplayEvent(Base):
    __tablename__ = "replay_events"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("incidents.id"), index=True)
    frame_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("replay_frames.id"), index=True)
    event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    event_type: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(32))
    source: Mapped[str] = mapped_column(String(128))
    payload_json: Mapped[str | None] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
