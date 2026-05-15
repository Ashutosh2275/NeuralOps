"""Intelligence layer schema

Revision ID: 002
Revises: 001
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "topology_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("version", sa.Integer(), server_default="1"),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("graph_json", sa.Text(), nullable=False),
        sa.Column("diff_json", sa.Text()),
        sa.Column("node_count", sa.Integer(), server_default="0"),
        sa.Column("edge_count", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "correlation_groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("namespace", sa.String(128)),
        sa.Column("trigger", sa.String(64)),
        sa.Column("severity", sa.String(32)),
        sa.Column("event_count", sa.Integer(), server_default="0"),
        sa.Column("related_event_ids_json", sa.Text()),
        sa.Column("dependency_context_json", sa.Text()),
        sa.Column("confidence_score", sa.Float(), server_default="0.5"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "ai_insights",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), index=True),
        sa.Column("agent_type", sa.String(64)),
        sa.Column("insight_type", sa.String(64)),
        sa.Column("title", sa.String(512)),
        sa.Column("content", sa.Text()),
        sa.Column("confidence", sa.Float(), server_default="0.7"),
        sa.Column("metadata_json", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "replay_frames",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), index=True),
        sa.Column("frame_index", sa.Integer()),
        sa.Column("timestamp", sa.DateTime(timezone=True), index=True),
        sa.Column("event_count", sa.Integer(), server_default="0"),
        sa.Column("topology_state_json", sa.Text()),
        sa.Column("events_json", sa.Text()),
    )
    op.create_table(
        "replay_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), index=True),
        sa.Column("frame_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("replay_frames.id"), index=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("event_type", sa.String(64)),
        sa.Column("severity", sa.String(32)),
        sa.Column("source", sa.String(128)),
        sa.Column("payload_json", sa.Text()),
        sa.Column("timestamp", sa.DateTime(timezone=True), index=True),
    )


def downgrade() -> None:
    for t in ("replay_events", "replay_frames", "ai_insights", "correlation_groups", "topology_versions"):
        op.drop_table(t)
