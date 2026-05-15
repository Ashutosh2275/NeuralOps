"""Initial SentinelOps schema

Revision ID: 001
Revises:
Create Date: 2026-05-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clusters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(128), unique=True, nullable=False),
        sa.Column("api_server", sa.String(512)),
        sa.Column("context", sa.String(256)),
        sa.Column("status", sa.String(32), server_default="active"),
        sa.Column("metadata_json", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "pods",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clusters.id")),
        sa.Column("namespace", sa.String(128), nullable=False, index=True),
        sa.Column("name", sa.String(253), nullable=False, index=True),
        sa.Column("node_name", sa.String(253)),
        sa.Column("phase", sa.String(32), server_default="Unknown"),
        sa.Column("owner_kind", sa.String(64)),
        sa.Column("owner_name", sa.String(253)),
        sa.Column("labels_json", sa.Text()),
        sa.Column("restart_count", sa.Integer(), server_default="0"),
        sa.Column("cpu_limit_millicores", sa.Integer()),
        sa.Column("memory_limit_bytes", sa.Integer()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "pod_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pod_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pods.id"), index=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), index=True),
        sa.Column("cpu_usage_millicores", sa.Float()),
        sa.Column("memory_usage_bytes", sa.Float()),
        sa.Column("cpu_percent", sa.Float()),
        sa.Column("memory_percent", sa.Float()),
        sa.Column("network_rx_bytes", sa.Float()),
        sa.Column("network_tx_bytes", sa.Float()),
        sa.Column("disk_usage_bytes", sa.Float()),
    )
    op.create_table(
        "services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("namespace", sa.String(128), nullable=False, index=True),
        sa.Column("name", sa.String(253), nullable=False, index=True),
        sa.Column("service_type", sa.String(32), server_default="ClusterIP"),
        sa.Column("selector_json", sa.Text()),
        sa.Column("ports_json", sa.Text()),
        sa.Column("labels_json", sa.Text()),
        sa.Column("health_status", sa.String(32), server_default="unknown"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "dependency_edges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("source_namespace", sa.String(128)),
        sa.Column("source_name", sa.String(253)),
        sa.Column("source_kind", sa.String(64), server_default="Pod"),
        sa.Column("target_namespace", sa.String(128)),
        sa.Column("target_name", sa.String(253)),
        sa.Column("target_kind", sa.String(64), server_default="Service"),
        sa.Column("edge_type", sa.String(64)),
        sa.Column("confidence", sa.Float(), server_default="0.5"),
        sa.Column("discovery_method", sa.String(64)),
        sa.Column("metadata_json", sa.Text()),
        sa.Column("discovered_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "topology_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), index=True),
        sa.Column("graph_json", sa.Text(), nullable=False),
        sa.Column("node_count", sa.Integer(), server_default="0"),
        sa.Column("edge_count", sa.Integer(), server_default="0"),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), index=True),
    )
    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clusters.id")),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("status", sa.String(32), server_default="open", index=True),
        sa.Column("severity", sa.String(32), server_default="warning"),
        sa.Column("root_cause", sa.Text()),
        sa.Column("root_service", sa.String(253)),
        sa.Column("confidence_score", sa.Float()),
        sa.Column("affected_services_json", sa.Text()),
        sa.Column("cascade_chain_json", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "incident_timeline",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), index=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), index=True),
        sa.Column("event_type", sa.String(64)),
        sa.Column("title", sa.String(512)),
        sa.Column("description", sa.Text()),
        sa.Column("source", sa.String(128)),
        sa.Column("severity", sa.String(32), server_default="info"),
        sa.Column("metadata_json", sa.Text()),
    )
    op.create_table(
        "incident_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), index=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("stream_message_id", sa.String(64)),
        sa.Column("event_type", sa.String(64)),
        sa.Column("payload_json", sa.Text()),
        sa.Column("timestamp", sa.DateTime(timezone=True), index=True),
    )
    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), index=True),
        sa.Column("agent_type", sa.String(64)),
        sa.Column("priority", sa.Integer(), server_default="2"),
        sa.Column("title", sa.String(512)),
        sa.Column("description", sa.Text()),
        sa.Column("action_type", sa.String(64)),
        sa.Column("kubectl_command", sa.Text()),
        sa.Column("confidence", sa.Float(), server_default="0.7"),
        sa.Column("status", sa.String(32), server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    for table in (
        "recommendations",
        "incident_events",
        "incident_timeline",
        "incidents",
        "topology_snapshots",
        "dependency_edges",
        "services",
        "pod_metrics",
        "pods",
        "clusters",
    ):
        op.drop_table(table)
