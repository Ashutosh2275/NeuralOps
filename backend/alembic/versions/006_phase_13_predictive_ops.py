"""Phase 13 - Predictive Autonomous Operations Platform

Revision ID: 006
Revises: 005
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Failure predictions table
    op.create_table(
        "failure_predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clusters.id"), index=True),
        sa.Column("incident_type", sa.String(64), index=True),
        sa.Column("probability", sa.Float()),
        sa.Column("confidence", sa.Float()),
        sa.Column("time_to_failure_hours", sa.Integer()),
        sa.Column("severity_forecast", sa.String(32)),
        sa.Column("affected_services", postgresql.ARRAY(sa.String)),
        sa.Column("reasoning", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), index=True),
    )

    # Infrastructure memory table
    op.create_table(
        "infrastructure_memory",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clusters.id"), index=True),
        sa.Column("memory_type", sa.String(64), index=True),
        sa.Column("key", sa.String(512), index=True),
        sa.Column("value", postgresql.JSON()),
        sa.Column("source_incident_id", postgresql.UUID(as_uuid=True)),
        sa.Column("confidence", sa.Float()),
        sa.Column("last_updated", sa.DateTime(timezone=True)),
    )

    # Remediation workflows table
    op.create_table(
        "remediation_workflows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), index=True),
        sa.Column("status", sa.String(32), index=True),
        sa.Column("steps", postgresql.JSON()),
        sa.Column("confidence", sa.Float()),
        sa.Column("current_step", sa.Integer()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )

    # K8s pressure analysis table
    op.create_table(
        "k8s_pressure_analysis",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clusters.id"), index=True),
        sa.Column("namespace", sa.String(253), index=True),
        sa.Column("resource_type", sa.String(64)),
        sa.Column("pressure_type", sa.String(64), index=True),
        sa.Column("saturation_percent", sa.Float()),
        sa.Column("affected_pods", postgresql.ARRAY(sa.String)),
        sa.Column("mitigation_recommendation", sa.Text()),
        sa.Column("detected_at", sa.DateTime(timezone=True), index=True),
    )

    # Create indexes for better query performance
    op.create_index("ix_failures_cluster_type", "failure_predictions", ["cluster_id", "incident_type"])
    op.create_index("ix_failures_created", "failure_predictions", ["created_at"])
    op.create_index("ix_memory_cluster_type", "infrastructure_memory", ["cluster_id", "memory_type"])
    op.create_index("ix_workflows_incident_status", "remediation_workflows", ["incident_id", "status"])
    op.create_index("ix_k8s_cluster_namespace", "k8s_pressure_analysis", ["cluster_id", "namespace"])


def downgrade() -> None:
    # Drop indexes
    for idx in [
        "ix_k8s_cluster_namespace",
        "ix_workflows_incident_status",
        "ix_memory_cluster_type",
        "ix_failures_created",
        "ix_failures_cluster_type",
    ]:
        try:
            op.drop_index(idx)
        except Exception:
            pass

    # Drop tables in reverse order
    op.drop_table("k8s_pressure_analysis")
    op.drop_table("remediation_workflows")
    op.drop_table("infrastructure_memory")
    op.drop_table("failure_predictions")
