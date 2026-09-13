from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sentinelops.core.database import Base


class IncidentForecast(Base):
    __tablename__ = "incident_forecasts"
    __table_args__ = {'extend_existing': True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    cluster_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("clusters.id"), index=True)

    forecast_type: Mapped[str] = mapped_column(String(64))
    target_service: Mapped[str] = mapped_column(String(253))
    target_pod: Mapped[str | None] = mapped_column(String(253))

    probability: Mapped[float] = mapped_column(Float)
    confidence_score: Mapped[float] = mapped_column(Float)
    severity_prediction: Mapped[str] = mapped_column(String(32))

    forecast_horizon_seconds: Mapped[int] = mapped_column(Integer)
    reasoning: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    forecast_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verified: Mapped[bool] = mapped_column(default=False)

    cluster: Mapped["Cluster"] = relationship("Cluster")  # noqa: F821


class IncidentAncestry(Base):
    __tablename__ = "incident_ancestry"
    __table_args__ = {'extend_existing': True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("incidents.id"), index=True)
    root_incident_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("incidents.id"))

    ancestry_depth: Mapped[int] = mapped_column(Integer)
    amplification_factor: Mapped[float] = mapped_column(Float)
    evolution_chain_json: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    incident: Mapped["Incident"] = relationship("Incident", foreign_keys=[incident_id])  # noqa: F821
    root_incident: Mapped["Incident"] = relationship("Incident", foreign_keys=[root_incident_id])  # noqa: F821

    @property
    def evolution_chain(self) -> list[dict]:
        import json
        if not self.evolution_chain_json:
            return []
        try:
            return json.loads(self.evolution_chain_json)
        except Exception:
            return []


class ServiceHealthScore(Base):
    __tablename__ = "service_health_scores"
    __table_args__ = {'extend_existing': True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    cluster_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("clusters.id"), index=True)
    service_name: Mapped[str] = mapped_column(String(253), index=True)

    uptime_score: Mapped[float] = mapped_column(Float)
    stability_score: Mapped[float] = mapped_column(Float)
    dependency_score: Mapped[float] = mapped_column(Float)
    resource_score: Mapped[float] = mapped_column(Float)

    overall_health: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(32))

    restart_frequency: Mapped[float] = mapped_column(Float)
    incident_frequency: Mapped[float] = mapped_column(Float)
    recovery_time_avg_seconds: Mapped[float] = mapped_column(Float)

    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)


class K8sResourceIntelligence(Base):
    __tablename__ = "k8s_resource_intelligence"
    __table_args__ = {'extend_existing': True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    cluster_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("clusters.id"), index=True)

    namespace: Mapped[str] = mapped_column(String(253), index=True)
    resource_type: Mapped[str] = mapped_column(String(64))
    pressure_type: Mapped[str] = mapped_column(String(64))

    pressure_score: Mapped[float] = mapped_column(Float)
    saturation_percent: Mapped[float] = mapped_column(Float)

    affected_workloads: Mapped[str] = mapped_column(Text)
    mitigation_json: Mapped[str] = mapped_column(Text)

    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)


class InfrastructureTimeline(Base):
    __tablename__ = "infrastructure_timelines"
    __table_args__ = {'extend_existing': True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    cluster_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("clusters.id"), index=True)

    event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    parent_event_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))

    event_type: Mapped[str] = mapped_column(String(64))
    source_entity: Mapped[str] = mapped_column(String(253))
    affected_entities: Mapped[str] = mapped_column(Text)

    causality_score: Mapped[float] = mapped_column(Float)
    lineage_depth: Mapped[int] = mapped_column(Integer)

    metadata_json: Mapped[str] = mapped_column(Text)

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class AIConfidenceValidation(Base):
    __tablename__ = "ai_confidence_validations"
    __table_args__ = {'extend_existing': True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("incidents.id"), index=True)

    rca_reasoning: Mapped[str] = mapped_column(Text)
    confidence_score: Mapped[float] = mapped_column(Float)

    validation_checks_json: Mapped[str] = mapped_column(Text)
    passed_checks: Mapped[int] = mapped_column(Integer)
    failed_checks: Mapped[int] = mapped_column(Integer)

    is_hallucination: Mapped[bool] = mapped_column(default=False)
    is_valid: Mapped[bool] = mapped_column(default=True)

    validation_details_json: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class RemediationOrchestration(Base):
    __tablename__ = "remediation_orchestrations"
    __table_args__ = {'extend_existing': True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("incidents.id"), index=True)

    workflow_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32))

    step_count: Mapped[int] = mapped_column(Integer)
    completed_steps: Mapped[int] = mapped_column(Integer)

    rollback_required: Mapped[bool] = mapped_column(default=False)
    confidence_score: Mapped[float] = mapped_column(Float)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ExecutiveMetrics(Base):
    __tablename__ = "executive_metrics"
    __table_args__ = {'extend_existing': True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    cluster_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("clusters.id"), index=True)

    mttr_seconds: Mapped[float] = mapped_column(Float)
    mttd_seconds: Mapped[float] = mapped_column(Float)
    incident_frequency_per_day: Mapped[float] = mapped_column(Float)

    uptime_percent: Mapped[float] = mapped_column(Float)
    sla_compliance_percent: Mapped[float] = mapped_column(Float)

    predicted_uptime_24h: Mapped[float] = mapped_column(Float)
    predicted_incidents_24h: Mapped[int] = mapped_column(Integer)

    reliability_score: Mapped[float] = mapped_column(Float)
    operational_efficiency_score: Mapped[float] = mapped_column(Float)

    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
