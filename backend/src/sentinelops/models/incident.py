from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sentinelops.core.database import Base


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = {'extend_existing': True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    cluster_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("clusters.id"))
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="open", index=True)
    severity: Mapped[str] = mapped_column(String(32), default="warning")
    root_cause: Mapped[str | None] = mapped_column(Text)
    root_service: Mapped[str | None] = mapped_column(String(253))
    confidence_score: Mapped[float | None] = mapped_column(Float)
    affected_services_json: Mapped[str | None] = mapped_column(Text)
    cascade_chain_json: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    cluster: Mapped["Cluster"] = relationship("Cluster", back_populates="incidents")  # noqa: F821
    timeline: Mapped[list["IncidentTimeline"]] = relationship("IncidentTimeline", back_populates="incident")
    events: Mapped[list["IncidentEvent"]] = relationship("IncidentEvent", back_populates="incident")


class IncidentTimeline(Base):
    __tablename__ = "incident_timeline"
    __table_args__ = {'extend_existing': True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("incidents.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    event_type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(128))
    severity: Mapped[str] = mapped_column(String(32), default="info")
    metadata_json: Mapped[str | None] = mapped_column(Text)

    incident: Mapped["Incident"] = relationship("Incident", back_populates="timeline")


class IncidentEvent(Base):
    __tablename__ = "incident_events"
    __table_args__ = {'extend_existing': True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("incidents.id"), index=True)
    event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    stream_message_id: Mapped[str | None] = mapped_column(String(64))
    event_type: Mapped[str] = mapped_column(String(64))
    payload_json: Mapped[str | None] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    incident: Mapped["Incident"] = relationship("Incident", back_populates="events")
