"""Topology graph node/edge persistence

Revision ID: 003
Revises: 002
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "topology_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("topology_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topology_versions.id"), index=True),
        sa.Column("node_id", sa.String(512), index=True),
        sa.Column("namespace", sa.String(128), index=True),
        sa.Column("kind", sa.String(64), index=True),
        sa.Column("name", sa.String(256)),
        sa.Column("health", sa.String(32), default="unknown"),
        sa.Column("labels_json", sa.Text()),
        sa.Column("metadata_json", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "topology_edges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("topology_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topology_versions.id"), index=True),
        sa.Column("source_node_id", sa.String(512), index=True),
        sa.Column("target_node_id", sa.String(512), index=True),
        sa.Column("edge_type", sa.String(64)),
        sa.Column("confidence", sa.Float(), default=0.5),
        sa.Column("discovery_method", sa.String(64)),
        sa.Column("health", sa.String(32), default="healthy"),
        sa.Column("metadata_json", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "dependency_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("source_node_id", sa.String(512), index=True),
        sa.Column("target_node_id", sa.String(512), index=True),
        sa.Column("influence_score", sa.Float(), default=0.5),
        sa.Column("blast_radius", sa.Integer(), default=0),
        sa.Column("propagation_depth", sa.Integer(), default=1),
        sa.Column("last_updated", sa.DateTime(timezone=True)),
    )

    op.create_index("ix_topology_nodes_cluster_version", "topology_nodes", ["cluster_id", "topology_version_id"])
    op.create_index("ix_topology_edges_cluster_version", "topology_edges", ["cluster_id", "topology_version_id"])
    op.create_index("ix_dependency_scores_source_target", "dependency_scores", ["source_node_id", "target_node_id"])


def downgrade() -> None:
    for idx in ("ix_topology_nodes_cluster_version", "ix_topology_edges_cluster_version", "ix_dependency_scores_source_target"):
        try:
            op.drop_index(idx)
        except Exception:
            pass

    for t in ("dependency_scores", "topology_edges", "topology_nodes"):
        op.drop_table(t)
