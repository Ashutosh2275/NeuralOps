"""AI agents and reasoning storage

Revision ID: 004
Revises: 003
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_insights",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), index=True),
        sa.Column("agent_type", sa.String(64), index=True),
        sa.Column("insight_type", sa.String(64)),
        sa.Column("title", sa.String(512)),
        sa.Column("content", sa.Text()),
        sa.Column("confidence", sa.Float(), default=0.7),
        sa.Column("reasoning", sa.Text()),
        sa.Column("metadata_json", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "ai_reasoning_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), index=True),
        sa.Column("agent_type", sa.String(64), index=True),
        sa.Column("prompt", sa.Text()),
        sa.Column("response", sa.Text()),
        sa.Column("tokens_used", sa.Integer(), default=0),
        sa.Column("latency_ms", sa.Integer(), default=0),
        sa.Column("model_used", sa.String(128)),
        sa.Column("success", sa.Boolean(), default=True),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "ai_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), index=True),
        sa.Column("agent_type", sa.String(64)),
        sa.Column("priority", sa.Integer(), default=2),
        sa.Column("title", sa.String(512)),
        sa.Column("description", sa.Text()),
        sa.Column("action_type", sa.String(64)),
        sa.Column("kubectl_command", sa.Text()),
        sa.Column("confidence", sa.Float(), default=0.7),
        sa.Column("risk_score", sa.Float(), default=0.3),
        sa.Column("blast_radius_impact", sa.String(32)),
        sa.Column("reasoning", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "incident_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), index=True),
        sa.Column("executive_summary", sa.Text()),
        sa.Column("technical_explanation", sa.Text()),
        sa.Column("timeline_summary", sa.Text()),
        sa.Column("impact_analysis", sa.Text()),
        sa.Column("remediation_steps", sa.Text()),
        sa.Column("generated_by", sa.String(128)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "infrastructure_memory",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("memory_type", sa.String(64), index=True),
        sa.Column("key", sa.String(512), index=True),
        sa.Column("value_json", sa.Text()),
        sa.Column("source_incident_id", postgresql.UUID(as_uuid=True)),
        sa.Column("confidence", sa.Float(), default=0.7),
        sa.Column("last_updated", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "anomaly_patterns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("pattern_type", sa.String(64), index=True),
        sa.Column("service_name", sa.String(256), index=True),
        sa.Column("pattern_data_json", sa.Text()),
        sa.Column("occurrence_count", sa.Integer(), default=1),
        sa.Column("severity", sa.String(32)),
        sa.Column("last_seen", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_index("ix_ai_insights_incident_agent", "ai_insights", ["incident_id", "agent_type"])
    op.create_index("ix_ai_reasoning_logs_incident_agent", "ai_reasoning_logs", ["incident_id", "agent_type"])
    op.create_index("ix_infrastructure_memory_cluster_type", "infrastructure_memory", ["cluster_id", "memory_type"])
    op.create_index("ix_anomaly_patterns_cluster_service", "anomaly_patterns", ["cluster_id", "service_name"])


def downgrade() -> None:
    for idx in (
        "ix_ai_insights_incident_agent",
        "ix_ai_reasoning_logs_incident_agent",
        "ix_infrastructure_memory_cluster_type",
        "ix_anomaly_patterns_cluster_service",
    ):
        try:
            op.drop_index(idx)
        except Exception:
            pass

    for t in (
        "anomaly_patterns",
        "infrastructure_memory",
        "incident_summaries",
        "ai_recommendations",
        "ai_reasoning_logs",
        "ai_insights",
    ):
        op.drop_table(t)
