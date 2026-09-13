import json
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sentinelops.core.logging import get_logger
from sentinelops.engines.dependency import DependencyIntelligenceEngine
from sentinelops.engines.topology import TopologySnapshotEngine
from sentinelops.models.dependency import DependencyEdge, TopologySnapshot
from sentinelops.models.intelligence import TopologyVersion
from sentinelops.models.topology import TopologyNode, TopologyEdge, DependencyScore

log = get_logger(__name__)


class TopologyService:
    """Manages topology versioning, persistence, and health propagation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._engine = DependencyIntelligenceEngine()
        self._snapshot_engine = TopologySnapshotEngine(self._engine)

    @property
    def dependency_engine(self) -> DependencyIntelligenceEngine:
        return self._engine

    async def get_latest_snapshot(self, cluster_id: UUID) -> TopologySnapshot | None:
        result = await self._session.execute(
            select(TopologySnapshot)
            .where(TopologySnapshot.cluster_id == cluster_id)
            .order_by(TopologySnapshot.snapshot_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_graph(self, cluster_id: UUID) -> dict:
        snapshot = await self.get_latest_snapshot(cluster_id)
        if snapshot:
            return json.loads(snapshot.graph_json)
        return self._engine.to_snapshot_json()

    async def capture_snapshot(self, cluster_id: UUID, incident_id: UUID | None = None) -> TopologySnapshot:
        return await self._snapshot_engine.capture(self._session, cluster_id, incident_id)

    async def load_edges_from_db(self, cluster_id: UUID) -> int:
        result = await self._session.execute(
            select(DependencyEdge).where(DependencyEdge.cluster_id == cluster_id)
        )
        edges = result.scalars().all()
        for edge in edges:
            self._engine.add_edge(
                edge.source_namespace, edge.source_name, edge.source_kind,
                edge.target_namespace, edge.target_name, edge.target_kind,
                edge.edge_type, edge.confidence, edge.discovery_method,
            )
        return len(edges)

    async def create_version_snapshot(
        self,
        cluster_id: UUID,
        snapshot_json: dict,
    ) -> TopologyVersion:
        """Create a new topology version from a snapshot."""
        prev_version = await self._get_latest_version(cluster_id)
        version_num = (prev_version.version if prev_version else 0) + 1

        diff = {}
        if prev_version:
            prev_graph = json.loads(prev_version.graph_json or "{}")
            diff = self._engine.diff_snapshots(prev_graph, snapshot_json)

        topology_version = TopologyVersion(
            id=uuid4(),
            cluster_id=cluster_id,
            version=version_num,
            graph_json=json.dumps(snapshot_json),
            diff_json=json.dumps(diff),
            node_count=len(snapshot_json.get("nodes", [])),
            edge_count=len(snapshot_json.get("edges", [])),
            created_at=datetime.utcnow(),
        )
        self._session.add(topology_version)
        await self._session.flush()

        await self._persist_nodes(cluster_id, topology_version.id, snapshot_json.get("nodes", []))
        await self._persist_edges(cluster_id, topology_version.id, snapshot_json.get("edges", []))

        return topology_version

    async def _persist_nodes(
        self,
        cluster_id: UUID,
        version_id: UUID,
        nodes: list[dict],
    ) -> None:
        """Persist topology nodes to database."""
        for node in nodes:
            node_id = node.get("id", "")
            ns = node.get("namespace", "default")
            kind = node.get("kind", "Unknown")
            name = node.get("name", "unknown")

            topo_node = TopologyNode(
                id=uuid4(),
                cluster_id=cluster_id,
                topology_version_id=version_id,
                node_id=node_id,
                namespace=ns,
                kind=kind,
                name=name,
                health=node.get("health", "unknown"),
                labels_json=json.dumps(node.get("labels", {})),
                metadata_json=json.dumps({k: v for k, v in node.items() if k not in ("id", "namespace", "kind", "name", "health", "labels")}),
                created_at=datetime.utcnow(),
            )
            self._session.add(topo_node)

    async def _persist_edges(
        self,
        cluster_id: UUID,
        version_id: UUID,
        edges: list[dict],
    ) -> None:
        """Persist topology edges to database."""
        for edge in edges:
            source = edge.get("source", "")
            target = edge.get("target", "")
            topo_edge = TopologyEdge(
                id=uuid4(),
                cluster_id=cluster_id,
                topology_version_id=version_id,
                source_node_id=source,
                target_node_id=target,
                edge_type=edge.get("edge_type", "depends_on"),
                confidence=edge.get("confidence", 0.5),
                discovery_method=edge.get("method", "discovered"),
                health=edge.get("health", "healthy"),
                metadata_json=json.dumps(edge.get("metadata", {})),
                created_at=datetime.utcnow(),
            )
            self._session.add(topo_edge)

    async def update_dependency_scores(
        self,
        cluster_id: UUID,
        root_node: str,
    ) -> None:
        """Update dependency influence scores from a root node."""
        blast = self._engine.blast_radius(root_node)

        for affected_node in blast.affected_nodes:
            influence = blast.influence_scores.get(affected_node, 0.5)

            existing = await self._session.execute(
                select(DependencyScore).where(
                    (DependencyScore.cluster_id == cluster_id) &
                    (DependencyScore.source_node_id == root_node) &
                    (DependencyScore.target_node_id == affected_node)
                )
            )
            score = existing.scalars().first()

            if score:
                score.influence_score = influence
                score.blast_radius = blast.affected_count
                score.last_updated = datetime.utcnow()
            else:
                score = DependencyScore(
                    id=uuid4(),
                    cluster_id=cluster_id,
                    source_node_id=root_node,
                    target_node_id=affected_node,
                    influence_score=influence,
                    blast_radius=blast.affected_count,
                    propagation_depth=blast.max_depth,
                    last_updated=datetime.utcnow(),
                )
                self._session.add(score)

    async def get_live_topology(self, cluster_id: UUID) -> dict:
        """Get the latest topology version with detailed metadata."""
        latest = await self._get_latest_version(cluster_id)
        graph = json.loads(latest.graph_json or "{}") if latest else {}

        if not latest or not graph.get("nodes"):
            try:
                from sentinelops.collectors.k8s_collector import KubernetesCollector
                k8s = KubernetesCollector()
                data = await k8s.collect_all("sentinelops-e2e")
                topo_events = data.get("topology", [])
                if topo_events:
                    ctx = topo_events[0].get("topology_context", {})
                    nodes = ctx.get("nodes", [])
                    edges = ctx.get("edges", [])
                    return {
                        "nodes": nodes,
                        "edges": edges,
                        "version": 1,
                        "generated_at": datetime.utcnow().isoformat(),
                    }
            except Exception:
                pass
            return {"nodes": [], "edges": [], "version": 0, "generated_at": datetime.utcnow().isoformat()}

        nodes_result = await self._session.execute(
            select(TopologyNode)
            .where(TopologyNode.topology_version_id == latest.id)
        )
        nodes_meta = {n.node_id: {"health": n.health, "labels": json.loads(n.labels_json or "{}")} for n in nodes_result.scalars().all()}

        for node in graph.get("nodes", []):
            meta = nodes_meta.get(node["id"], {})
            node["health"] = meta.get("health", "unknown")
            node["labels"] = meta.get("labels", {})

        edges_result = await self._session.execute(
            select(TopologyEdge)
            .where(TopologyEdge.topology_version_id == latest.id)
        )
        edges_meta = {(e.source_node_id, e.target_node_id): e for e in edges_result.scalars().all()}

        for edge in graph.get("edges", []):
            meta = edges_meta.get((edge["source"], edge["target"]))
            if meta:
                edge["health"] = meta.health
                edge["confidence"] = meta.confidence

        return {
            "nodes": graph.get("nodes", []),
            "edges": graph.get("edges", []),
            "version": latest.version,
            "generated_at": latest.created_at.isoformat(),
        }

    async def list_topology_versions(
        self,
        cluster_id: UUID,
        limit: int = 10,
    ) -> list[dict]:
        """List recent topology versions."""
        result = await self._session.execute(
            select(TopologyVersion)
            .where(TopologyVersion.cluster_id == cluster_id)
            .order_by(TopologyVersion.version.desc())
            .limit(limit)
        )
        versions = result.scalars().all()
        return [
            {
                "version": v.version,
                "node_count": v.node_count,
                "edge_count": v.edge_count,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "diff": json.loads(v.diff_json or "{}"),
            }
            for v in versions
        ]

    async def _get_latest_version(self, cluster_id: UUID) -> TopologyVersion | None:
        """Get the latest topology version for a cluster."""
        result = await self._session.execute(
            select(TopologyVersion)
            .where(TopologyVersion.cluster_id == cluster_id)
            .order_by(TopologyVersion.version.desc())
            .limit(1)
        )
        return result.scalars().first()
