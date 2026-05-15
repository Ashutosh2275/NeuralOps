"""Add Phase 11 simulation and remediation tables

Revision ID: 002_phase_11_systems
Revises:
Create Date: 2026-05-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_phase_11_systems'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create simulated_incidents table
    op.create_table(
        'simulated_incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cluster_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('simulation_type', sa.String(64), nullable=False),
        sa.Column('severity', sa.String(32), nullable=False, server_default='moderate'),
        sa.Column('namespace', sa.String(253), nullable=False),
        sa.Column('target_pods', sa.Text(), nullable=False),
        sa.Column('target_services', sa.Text(), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=False),
        sa.Column('cascading_probability', sa.Float(), nullable=False, server_default='0.3'),
        sa.Column('metadata_json', sa.Text(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['cluster_id'], ['clusters.id'], ),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_simulated_incidents_cluster_id', 'cluster_id'),
        sa.Index('ix_simulated_incidents_simulation_type', 'simulation_type'),
    )

    # Create remediation_actions table
    op.create_table(
        'remediation_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('simulation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_type', sa.String(64), nullable=False),
        sa.Column('target_pod', sa.String(253), nullable=True),
        sa.Column('target_service', sa.String(253), nullable=True),
        sa.Column('target_namespace', sa.String(253), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='pending'),
        sa.Column('ai_recommendation', sa.Text(), nullable=False),
        sa.Column('parameters_json', sa.Text(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['simulation_id'], ['simulated_incidents.id'], ),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_remediation_actions_simulation_id', 'simulation_id'),
        sa.Index('ix_remediation_actions_incident_id', 'incident_id'),
    )

    # Create infrastructure_scores table
    op.create_table(
        'infrastructure_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cluster_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cluster_health', sa.Float(), nullable=False),
        sa.Column('namespace_health', sa.Float(), nullable=False),
        sa.Column('service_health', sa.Float(), nullable=False),
        sa.Column('dependency_health', sa.Float(), nullable=False),
        sa.Column('incident_risk_score', sa.Float(), nullable=False),
        sa.Column('recovery_readiness_score', sa.Float(), nullable=False),
        sa.Column('ai_confidence_score', sa.Float(), nullable=False),
        sa.Column('operational_stability_score', sa.Float(), nullable=False),
        sa.Column('cascading_failure_probability', sa.Float(), nullable=False),
        sa.Column('overall_health', sa.Float(), nullable=False),
        sa.Column('namespace_scores_json', sa.Text(), nullable=False),
        sa.Column('service_scores_json', sa.Text(), nullable=False),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['cluster_id'], ['clusters.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_infrastructure_scores_cluster_id', 'cluster_id'),
        sa.Index('ix_infrastructure_scores_calculated_at', 'calculated_at'),
    )

    # Create blast_radius_events table
    op.create_table(
        'blast_radius_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('simulation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('origin_pod', sa.String(253), nullable=False),
        sa.Column('origin_namespace', sa.String(253), nullable=False),
        sa.Column('affected_services', sa.Text(), nullable=False),
        sa.Column('propagation_depth', sa.Integer(), nullable=False),
        sa.Column('degradation_intensity', sa.Float(), nullable=False),
        sa.Column('recovery_path_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['simulation_id'], ['simulated_incidents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_blast_radius_events_simulation_id', 'simulation_id'),
    )

    # Create replay_sessions table
    op.create_table(
        'replay_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('simulation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('frames_count', sa.Integer(), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=False),
        sa.Column('frames_json', sa.Text(), nullable=False),
        sa.Column('timeline_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.ForeignKeyConstraint(['simulation_id'], ['simulated_incidents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_replay_sessions_incident_id', 'incident_id'),
    )

    # Create recovery_timelines table
    op.create_table(
        'recovery_timelines',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('simulation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.String(64), nullable=False),
        sa.Column('title', sa.String(512), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('affected_services', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(32), nullable=False),
        sa.Column('recovery_estimate_seconds', sa.Integer(), nullable=False),
        sa.Column('actual_recovery_seconds', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('metadata_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.ForeignKeyConstraint(['simulation_id'], ['simulated_incidents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_recovery_timelines_incident_id', 'incident_id'),
        sa.Index('ix_recovery_timelines_event_type', 'event_type'),
    )


def downgrade() -> None:
    op.drop_index('ix_recovery_timelines_event_type', table_name='recovery_timelines')
    op.drop_index('ix_recovery_timelines_incident_id', table_name='recovery_timelines')
    op.drop_table('recovery_timelines')
    op.drop_index('ix_replay_sessions_incident_id', table_name='replay_sessions')
    op.drop_table('replay_sessions')
    op.drop_index('ix_blast_radius_events_simulation_id', table_name='blast_radius_events')
    op.drop_table('blast_radius_events')
    op.drop_index('ix_infrastructure_scores_calculated_at', table_name='infrastructure_scores')
    op.drop_index('ix_infrastructure_scores_cluster_id', table_name='infrastructure_scores')
    op.drop_table('infrastructure_scores')
    op.drop_index('ix_remediation_actions_incident_id', table_name='remediation_actions')
    op.drop_index('ix_remediation_actions_simulation_id', table_name='remediation_actions')
    op.drop_table('remediation_actions')
    op.drop_index('ix_simulated_incidents_simulation_type', table_name='simulated_incidents')
    op.drop_index('ix_simulated_incidents_cluster_id', table_name='simulated_incidents')
    op.drop_table('simulated_incidents')
