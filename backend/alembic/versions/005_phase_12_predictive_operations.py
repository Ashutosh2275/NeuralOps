"""Phase 12 - Enterprise incident intelligence and predictive operations

Revision ID: 005
Revises: 004
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "incident_forecasts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clusters.id"), index=True),
        sa.Column("forecast_type", sa.String(64), index=True),
        sa.Column("target_service", sa.String(253), index=True),
        sa.Column("target_pod", sa.String(253)),
        sa.Column("probability", sa.Float()),
        sa.Column("confidence_score", sa.Float()),
        sa.Column("severity_prediction", sa.String(32), index=True),
        sa.Column("forecast_horizon_seconds", sa.Integer()),
        sa.Column("reasoning", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), index=True),
        sa.Column("forecast_time", sa.DateTime(timezone=True), index=True),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("verified", sa.Boolean(), default=False),
    )

    op.create_table(
        "incident_ancestry",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), index=True),
        sa.Column("root_incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id")),
        sa.Column("ancestry_depth", sa.Integer()),
        sa.Column("amplification_factor", sa.Float()),
        sa.Column("evolution_chain_json", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "service_health_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clusters.id"), index=True),
        sa.Column("service_name", sa.String(253), index=True),
        sa.Column("uptime_score", sa.Float()),
        sa.Column("stability_score", sa.Float()),
        sa.Column("dependency_score", sa.Float()),
        sa.Column("resource_score", sa.Float()),
        sa.Column("overall_health", sa.Float(), index=True),
        sa.Column("risk_level", sa.String(32), index=True),
        sa.Column("restart_frequency", sa.Float()),
        sa.Column("incident_frequency", sa.Float()),
        sa.Column("recovery_time_avg_seconds", sa.Float()),
        sa.Column("calculated_at", sa.DateTime(timezone=True), index=True),
    )

    op.create_table(
        "k8s_resource_intelligence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clusters.id"), index=True),
        sa.Column("namespace", sa.String(253), index=True),
        sa.Column("resource_type", sa.String(64)),
        sa.Column("pressure_type", sa.String(64), index=True),
        sa.Column("pressure_score", sa.Float()),
        sa.Column("saturation_percent", sa.Float()),
        sa.Column("affected_workloads", sa.Text()),
        sa.Column("mitigation_json", sa.Text()),
        sa.Column("detected_at", sa.DateTime(timezone=True), index=True),
    )

    op.create_table(
        "infrastructure_timelines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clusters.id"), index=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("parent_event_id", postgresql.UUID(as_uuid=True)),
        sa.Column("event_type", sa.String(64), index=True),
        sa.Column("source_entity", sa.String(253)),
        sa.Column("affected_entities", sa.Text()),
        sa.Column("causality_score", sa.Float()),
        sa.Column("lineage_depth", sa.Integer()),
        sa.Column("metadata_json", sa.Text()),
        sa.Column("timestamp", sa.DateTime(timezone=True), index=True),
    )

    op.create_table(
        "ai_confidence_validations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), index=True),
        sa.Column("rca_reasoning", sa.Text()),
        sa.Column("confidence_score", sa.Float()),
        sa.Column("validation_checks_json", sa.Text()),
        sa.Column("passed_checks", sa.Integer()),
        sa.Column("failed_checks", sa.Integer()),
        sa.Column("is_hallucination", sa.Boolean(), default=False, index=True),
        sa.Column("is_valid", sa.Boolean(), default=True, index=True),
        sa.Column("validation_details_json", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "remediation_orchestrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), index=True),
        sa.Column("workflow_json", sa.Text()),
        sa.Column("status", sa.String(32), index=True),
        sa.Column("step_count", sa.Integer()),
        sa.Column("completed_steps", sa.Integer()),
        sa.Column("rollback_required", sa.Boolean(), default=False),
        sa.Column("confidence_score", sa.Float()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "executive_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clusters.id"), index=True),
        sa.Column("mttr_seconds", sa.Float()),
        sa.Column("mttd_seconds", sa.Float()),
        sa.Column("incident_frequency_per_day", sa.Float()),
        sa.Column("uptime_percent", sa.Float()),
        sa.Column("sla_compliance_percent", sa.Float()),
        sa.Column("predicted_uptime_24h", sa.Float()),
        sa.Column("predicted_incidents_24h", sa.Integer()),
        sa.Column("reliability_score", sa.Float()),
        sa.Column("operational_efficiency_score", sa.Float()),
        sa.Column("calculated_at", sa.DateTime(timezone=True), index=True),
    )

    op.create_index("ix_forecast_cluster_type", "incident_forecasts", ["cluster_id", "forecast_type"])
    op.create_index("ix_forecast_service_severity", "incident_forecasts", ["target_service", "severity_prediction"])
    op.create_index("ix_ancestry_incident_root", "incident_ancestry", ["incident_id", "root_incident_id"])
    op.create_index("ix_health_cluster_service", "service_health_scores", ["cluster_id", "service_name"])
    op.create_index("ix_health_risk_level", "service_health_scores", ["risk_level"])
    op.create_index("ix_k8s_cluster_namespace", "k8s_resource_intelligence", ["cluster_id", "namespace"])
    op.create_index("ix_timeline_cluster_type", "infrastructure_timelines", ["cluster_id", "event_type"])
    op.create_index("ix_timeline_causality", "infrastructure_timelines", ["causality_score"])
    op.create_index("ix_validation_incident_hallucination", "ai_confidence_validations", ["incident_id", "is_hallucination"])
    op.create_index("ix_remediation_status", "remediation_orchestrations", ["incident_id", "status"])
    op.create_index("ix_metrics_cluster_time", "executive_metrics", ["cluster_id", "calculated_at"])


def downgrade() -> None:
    indices = [
        "ix_metrics_cluster_time",
        "ix_remediation_status",
        "ix_validation_incident_hallucination",
        "ix_timeline_causality",
        "ix_timeline_cluster_type",
        "ix_k8s_cluster_namespace",
        "ix_health_risk_level",
        "ix_health_cluster_service",
        "ix_ancestry_incident_root",
        "ix_forecast_service_severity",
        "ix_forecast_cluster_type",
    ]

    for idx in indices:
        try:
            op.drop_index(idx)
        except Exception:
            pass

    tables = [
        "executive_metrics",
        "remediation_orchestrations",
        "ai_confidence_validations",
        "infrastructure_timelines",
        "k8s_resource_intelligence",
        "service_health_scores",
        "incident_ancestry",
        "incident_forecasts",
    ]

    for table in tables:
        op.drop_table(table)
