from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sentinelops.core.database import Base


class SimulationType(str, Enum):
    CPU_SPIKE = "cpu_spike"
    MEMORY_LEAK = "memory_leak"
    PVC_SATURATION = "pvc_saturation"
    DISK_IO_BOTTLENECK = "disk_io_bottleneck"
    PACKET_LOSS = "packet_loss"
    NETWORK_LATENCY = "network_latency"
    CRASHLOOP_BACKOFF = "crashloop_backoff"
    POD_RESTART_STORM = "pod_restart_storm"
    SERVICE_DEPENDENCY_FAILURE = "service_dependency_failure"
    DATABASE_BOTTLENECK = "database_bottleneck"
    API_GATEWAY_OVERLOAD = "api_gateway_overload"
    REDIS_CONGESTION = "redis_congestion"
    KAFKA_LAG = "kafka_lag"
    NAMESPACE_DEGRADATION = "namespace_degradation"
    CASCADING_MULTI_SERVICE = "cascading_multi_service"


class SimulationSeverity(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"


class SimulatedIncident(Base):
    __tablename__ = "simulated_incidents"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    cluster_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("clusters.id"), index=True)
    incident_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("incidents.id"))

    simulation_type: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(32), default="moderate")

    namespace: Mapped[str] = mapped_column(String(253))
    target_pods: Mapped[str] = mapped_column(Text)
    target_services: Mapped[str] = mapped_column(Text)

    duration_seconds: Mapped[int] = mapped_column(Integer)
    cascading_probability: Mapped[float] = mapped_column(Float, default=0.3)

    metadata_json: Mapped[str] = mapped_column(Text)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    cluster: Mapped["Cluster"] = relationship("Cluster")  # noqa: F821
    incident: Mapped["Incident"] = relationship("Incident")  # noqa: F821
    remediation_actions: Mapped[list["RemediationAction"]] = relationship("RemediationAction", back_populates="simulation")
    blast_radius_events: Mapped[list["BlastRadiusEvent"]] = relationship("BlastRadiusEvent", back_populates="simulation")


class RemediationAction(Base):
    __tablename__ = "remediation_actions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    simulation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("simulated_incidents.id"), index=True)
    incident_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("incidents.id"), index=True)

    action_type: Mapped[str] = mapped_column(String(64))
    target_pod: Mapped[str | None] = mapped_column(String(253))
    target_service: Mapped[str | None] = mapped_column(String(253))
    target_namespace: Mapped[str] = mapped_column(String(253))

    status: Mapped[str] = mapped_column(String(32), default="pending")
    ai_recommendation: Mapped[str] = mapped_column(Text)

    parameters_json: Mapped[str] = mapped_column(Text)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    simulation: Mapped["SimulatedIncident"] = relationship("SimulatedIncident", back_populates="remediation_actions")


class InfrastructureScore(Base):
    __tablename__ = "infrastructure_scores"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    cluster_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("clusters.id"), index=True)

    cluster_health: Mapped[float] = mapped_column(Float)
    namespace_health: Mapped[float] = mapped_column(Float)
    service_health: Mapped[float] = mapped_column(Float)
    dependency_health: Mapped[float] = mapped_column(Float)

    incident_risk_score: Mapped[float] = mapped_column(Float)
    recovery_readiness_score: Mapped[float] = mapped_column(Float)
    ai_confidence_score: Mapped[float] = mapped_column(Float)
    operational_stability_score: Mapped[float] = mapped_column(Float)
    cascading_failure_probability: Mapped[float] = mapped_column(Float)

    overall_health: Mapped[float] = mapped_column(Float)

    namespace_scores_json: Mapped[str] = mapped_column(Text)
    service_scores_json: Mapped[str] = mapped_column(Text)

    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)


class BlastRadiusEvent(Base):
    __tablename__ = "blast_radius_events"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    simulation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("simulated_incidents.id"), index=True)

    origin_pod: Mapped[str] = mapped_column(String(253))
    origin_namespace: Mapped[str] = mapped_column(String(253))

    affected_services: Mapped[str] = mapped_column(Text)
    propagation_depth: Mapped[int] = mapped_column(Integer)
    degradation_intensity: Mapped[float] = mapped_column(Float)

    recovery_path_json: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    simulation: Mapped["SimulatedIncident"] = relationship("SimulatedIncident", back_populates="blast_radius_events")


class ReplaySession(Base):
    __tablename__ = "replay_sessions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("incidents.id"), index=True)
    simulation_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("simulated_incidents.id"))

    frames_count: Mapped[int] = mapped_column(Integer)
    duration_seconds: Mapped[int] = mapped_column(Integer)

    frames_json: Mapped[str] = mapped_column(Text)
    timeline_json: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class RecoveryTimeline(Base):
    __tablename__ = "recovery_timelines"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("incidents.id"), index=True)
    simulation_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("simulated_incidents.id"))

    event_type: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str] = mapped_column(Text)

    affected_services: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(32))

    recovery_estimate_seconds: Mapped[int] = mapped_column(Integer)
    actual_recovery_seconds: Mapped[int | None] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(String(32))

    metadata_json: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
