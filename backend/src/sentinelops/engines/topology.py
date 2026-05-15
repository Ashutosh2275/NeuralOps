import json
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sentinelops.core.logging import get_logger
from sentinelops.engines.dependency import DependencyIntelligenceEngine
from sentinelops.models.dependency import TopologySnapshot
from sentinelops.models.intelligence import TopologyVersion

log = get_logger(__name__)


class TopologySnapshotEngine:
    """Topology versioning, diffs, and PostgreSQL persistence."""

    def __init__(self, dependency_engine: DependencyIntelligenceEngine | None = None) -> None:
        self._dependency = dependency_engine or DependencyIntelligenceEngine()

    @property
    def dependency_engine(self) -> DependencyIntelligenceEngine:
        return self._dependency

    async def capture(
        self,
        session: AsyncSession,
        cluster_id: UUID,
        incident_id: UUID | None = None,
    ) -> TopologySnapshot:
        graph = self._dependency.to_snapshot_json()
        snapshot = TopologySnapshot(
            id=uuid4(),
            cluster_id=cluster_id,
            snapshot_at=datetime.utcnow(),
            graph_json=json.dumps(graph),
            node_count=len(graph["nodes"]),
            edge_count=len(graph["edges"]),
            incident_id=incident_id,
        )
        session.add(snapshot)
        await session.flush()
        await self._create_version(session, cluster_id, graph, snapshot.id)
        log.info("topology_snapshot_captured", snapshot_id=str(snapshot.id), nodes=snapshot.node_count)
        return snapshot

    async def _create_version(
        self,
        session: AsyncSession,
        cluster_id: UUID,
        graph: dict,
        snapshot_id: UUID,
    ) -> TopologyVersion:
        result = await session.execute(
            select(TopologyVersion)
            .where(TopologyVersion.cluster_id == cluster_id)
            .order_by(TopologyVersion.version.desc())
            .limit(1)
        )
        prev = result.scalar_one_or_none()
        version_num = (prev.version + 1) if prev else 1
        diff = None
        if prev:
            diff = self._dependency.diff_snapshots(json.loads(prev.graph_json), graph)

        version = TopologyVersion(
            id=uuid4(),
            cluster_id=cluster_id,
            version=version_num,
            snapshot_id=snapshot_id,
            graph_json=json.dumps(graph),
            diff_json=json.dumps(diff) if diff else None,
            node_count=len(graph.get("nodes", [])),
            edge_count=len(graph.get("edges", [])),
        )
        session.add(version)
        await session.flush()
        return version

    async def get_latest_version(self, session: AsyncSession, cluster_id: UUID) -> TopologyVersion | None:
        result = await session.execute(
            select(TopologyVersion)
            .where(TopologyVersion.cluster_id == cluster_id)
            .order_by(TopologyVersion.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_graph_at_version(
        self, session: AsyncSession, cluster_id: UUID, version: int
    ) -> dict | None:
        result = await session.execute(
            select(TopologyVersion).where(
                TopologyVersion.cluster_id == cluster_id,
                TopologyVersion.version == version,
            )
        )
        row = result.scalar_one_or_none()
        return json.loads(row.graph_json) if row else None
