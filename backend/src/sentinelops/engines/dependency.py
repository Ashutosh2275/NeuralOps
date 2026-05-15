import json
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

import networkx as nx

from sentinelops.core.logging import get_logger
from sentinelops.events.schemas import TopologyEvent

log = get_logger(__name__)


@dataclass
class BlastRadiusResult:
    root_node: str
    affected_nodes: list[str]
    affected_count: int
    max_depth: int
    influence_scores: dict[str, float] = field(default_factory=dict)


@dataclass
class DependencyPath:
    path: list[str]
    total_confidence: float
    hops: int


@dataclass
class CascadeResult:
    origin_node: str
    cascade_chain: list[dict[str, str | int | float]]
    affected_count: int
    propagation_depth: int
    escalation_factor: float


@dataclass
class HealthPropagation:
    node_id: str
    original_health: str
    propagated_health: str
    propagation_path: list[str]
    influence_score: float


class DependencyIntelligenceEngine:
    """Enhanced dependency discovery, traversal, blast radius, cascade analysis, and health propagation."""

    EDGE_RULES = (
        ("Pod", "Service", "routes_to", 0.85, "label_selector"),
        ("Service", "Service", "calls", 0.7, "env_reference"),
        ("Pod", "PersistentVolumeClaim", "mounts", 0.9, "volume_mount"),
        ("Service", "Service", "cache_dependency", 0.75, "naming"),
        ("Deployment", "Service", "exposes", 0.95, "owner"),
        ("Ingress", "Service", "routes", 0.88, "ingress_rule"),
    )

    # Critical service multipliers for blast radius
    CRITICAL_SERVICES = {"postgres", "redis", "kafka", "elasticsearch", "vault"}
    CRITICAL_MULTIPLIER = 1.5

    def __init__(self) -> None:
        self._graph = nx.DiGraph()
        self._health_cache: dict[str, str] = {}
        self._last_snapshot = None

    def node_id(self, namespace: str, kind: str, name: str) -> str:
        return f"{namespace}/{kind}/{name}"

    def add_edge(
        self,
        source_ns: str,
        source_name: str,
        source_kind: str,
        target_ns: str,
        target_name: str,
        target_kind: str,
        edge_type: str,
        confidence: float = 0.5,
        method: str = "label_selector",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        source_id = self.node_id(source_ns, source_kind, source_name)
        target_id = self.node_id(target_ns, target_kind, target_name)
        self._graph.add_node(
            source_id,
            namespace=source_ns,
            kind=source_kind,
            name=source_name,
            health="unknown",
        )
        self._graph.add_node(
            target_id,
            namespace=target_ns,
            kind=target_kind,
            name=target_name,
            health="unknown",
        )
        self._graph.add_edge(
            source_id,
            target_id,
            edge_type=edge_type,
            confidence=confidence,
            method=method,
            health="healthy",
            metadata=metadata or {},
        )

    def ingest_k8s_snapshot(self, snapshot: dict[str, Any]) -> int:
        added = 0
        for node in snapshot.get("topology_context", {}).get("nodes", snapshot.get("nodes", [])):
            nid = node.get("id") or self.node_id(
                node.get("namespace", "default"),
                node.get("kind", "Unknown"),
                node.get("name", "unknown"),
            )
            self._graph.add_node(nid, **{k: v for k, v in node.items() if k != "id"})
            added += 1
        for edge in snapshot.get("topology_context", {}).get("edges", snapshot.get("edges", [])):
            src, tgt = edge.get("source"), edge.get("target")
            if src and tgt and not self._graph.has_edge(src, tgt):
                self._graph.add_edge(
                    src,
                    tgt,
                    edge_type=edge.get("edge_type", "depends_on"),
                    confidence=edge.get("confidence", 0.5),
                    method=edge.get("method", "discovered"),
                    health="healthy",
                )
                added += 1
        return added

    def discover_from_collector_data(
        self,
        pods: list[dict[str, Any]],
        services: list[dict[str, Any]],
        dependencies: list[dict[str, Any]],
    ) -> int:
        added = 0
        for dep in dependencies:
            self.add_edge(
                dep.get("namespace", "default"),
                dep.get("source_name", ""),
                dep.get("source_kind", "Pod"),
                dep.get("namespace", "default"),
                dep.get("target_name", ""),
                dep.get("target_kind", "Service"),
                dep.get("edge_type", "depends_on"),
                dep.get("confidence", 0.8),
                dep.get("discovery_method", "label_selector"),
            )
            added += 1
        for pod in pods:
            app = (pod.get("labels") or {}).get("app")
            for svc in services:
                if app and (svc.get("selector") or {}).get("app") == app:
                    self.add_edge(
                        pod["namespace"],
                        pod["pod_name"],
                        "Pod",
                        svc["namespace"],
                        svc["service_name"],
                        "Service",
                        "routes_to",
                        0.9,
                        "label_selector",
                    )
                    added += 1
            if "postgres" in pod.get("pod_name", "").lower():
                self.add_edge(
                    pod["namespace"], pod["pod_name"], "Pod",
                    pod["namespace"], "postgres", "Database",
                    "queries", 0.85, "naming",
                )
                added += 1
            if "redis" in pod.get("pod_name", "").lower():
                self.add_edge(
                    pod["namespace"], pod["pod_name"], "Pod",
                    pod["namespace"], "redis-cache", "Cache",
                    "cache_read", 0.8, "naming",
                )
                added += 1
        return added

    def bfs_downstream(self, root: str, max_depth: int = 5) -> list[str]:
        if root not in self._graph:
            return []
        visited: list[str] = []
        queue: deque[tuple[str, int]] = deque([(root, 0)])
        seen: set[str] = set()
        while queue:
            node, depth = queue.popleft()
            if node in seen or depth > max_depth:
                continue
            seen.add(node)
            if node != root:
                visited.append(node)
            for succ in self._graph.successors(node):
                queue.append((succ, depth + 1))
        return visited

    def dfs_downstream(self, root: str, max_depth: int = 5) -> list[str]:
        if root not in self._graph:
            return []
        visited: list[str] = []

        def _dfs(node: str, depth: int) -> None:
            if depth > max_depth:
                return
            for succ in self._graph.successors(node):
                if succ not in visited:
                    visited.append(succ)
                    _dfs(succ, depth + 1)

        _dfs(root, 0)
        return visited

    def shortest_dependency_path(self, source: str, target: str) -> DependencyPath | None:
        if source not in self._graph or target not in self._graph:
            return None
        try:
            path = nx.shortest_path(self._graph, source, target)
        except nx.NetworkXNoPath:
            return None
        confidences = [
            self._graph.edges[path[i], path[i + 1]].get("confidence", 0.5)
            for i in range(len(path) - 1)
        ]
        total = sum(confidences) / len(confidences) if confidences else 0.0
        return DependencyPath(path=path, total_confidence=total, hops=len(path) - 1)

    def blast_radius(self, root_node: str, max_depth: int = 5) -> BlastRadiusResult:
        affected = self.bfs_downstream(root_node, max_depth)
        scores: dict[str, float] = {}
        for i, node in enumerate(affected):
            depth_factor = 1.0 / (1 + i * 0.2)
            is_critical = self._is_critical_service(node)
            multiplier = self.CRITICAL_MULTIPLIER if is_critical else 1.0
            scores[node] = round(depth_factor * multiplier, 3)
        return BlastRadiusResult(
            root_node=root_node,
            affected_nodes=affected,
            affected_count=len(affected),
            max_depth=max_depth,
            influence_scores=scores,
        )

    def influence_chain_score(self, root: str) -> float:
        blast = self.blast_radius(root)
        if not blast.affected_nodes:
            return 0.0
        return min(1.0, 0.3 + 0.1 * len(blast.affected_nodes) + 0.05 * blast.max_depth)

    def get_upstream(self, node_id: str, depth: int = 3) -> list[str]:
        if node_id not in self._graph:
            return []
        ancestors: set[str] = set()
        queue: deque[tuple[str, int]] = deque([(node_id, 0)])
        while queue:
            node, d = queue.popleft()
            if d >= depth:
                continue
            for pred in self._graph.predecessors(node):
                if pred not in ancestors:
                    ancestors.add(pred)
                    queue.append((pred, d + 1))
        return list(ancestors)

    def get_downstream(self, node_id: str, depth: int = 3) -> list[str]:
        return self.bfs_downstream(node_id, depth)

    def find_cascade_path(self, root_node: str) -> list[dict[str, str | int | float]]:
        if root_node not in self._graph:
            return []
        chain: list[dict[str, str | int | float]] = []
        visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque([(root_node, 0)])
        while queue:
            node, order = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            parts = node.split("/")
            chain.append({
                "service": parts[-1] if len(parts) >= 3 else node,
                "order": order,
                "failure_mode": "origin" if order == 0 else "propagated",
                "influence": self.influence_chain_score(node),
            })
            for succ in sorted(self._graph.successors(node)):
                if succ not in visited:
                    queue.append((succ, order + 1))
        return chain

    def detect_cascading_failure(self, root_node: str) -> CascadeResult:
        """Detect potential cascading failure from an unhealthy node."""
        cascade_chain = self.find_cascade_path(root_node)
        blast = self.blast_radius(root_node)

        propagation_depth = 0
        for item in cascade_chain:
            if isinstance(item.get("order"), int):
                propagation_depth = max(propagation_depth, item["order"])

        escalation_factor = 1.0
        if blast.affected_count > 5:
            escalation_factor = 1.5
        if blast.affected_count > 10:
            escalation_factor = 2.0

        return CascadeResult(
            origin_node=root_node,
            cascade_chain=cascade_chain,
            affected_count=blast.affected_count,
            propagation_depth=propagation_depth,
            escalation_factor=escalation_factor,
        )

    def propagate_health(self, unhealthy_node: str, source_health: str = "critical") -> list[HealthPropagation]:
        """Propagate health status through edges with influence scoring."""
        if unhealthy_node not in self._graph:
            return []

        propagations: list[HealthPropagation] = []
        visited: set[str] = set()
        queue: deque[tuple[str, str, float, list[str]]] = deque([(unhealthy_node, source_health, 1.0, [unhealthy_node])])

        while queue:
            node, health_status, influence, path = queue.popleft()
            if node in visited or len(path) > 6:
                continue
            visited.add(node)

            if node != unhealthy_node:
                new_health = self._compute_propagated_health(health_status, influence)
                propagations.append(HealthPropagation(
                    node_id=node,
                    original_health=self._graph.nodes[node].get("health", "unknown"),
                    propagated_health=new_health,
                    propagation_path=path,
                    influence_score=round(influence, 3),
                ))

            for succ in self._graph.successors(node):
                edge_conf = self._graph.edges[node, succ].get("confidence", 0.5)
                new_influence = influence * edge_conf
                if succ not in visited and new_influence > 0.3:
                    queue.append((succ, health_status, new_influence, path + [succ]))

        return propagations

    def mark_unhealthy(self, node_id: str) -> None:
        if node_id in self._graph:
            self._graph.nodes[node_id]["health"] = "unhealthy"
            self._health_cache[node_id] = "unhealthy"

    def mark_healthy(self, node_id: str) -> None:
        if node_id in self._graph:
            self._graph.nodes[node_id]["health"] = "healthy"
            self._health_cache[node_id] = "healthy"

    def set_edge_health(self, source: str, target: str, health: str) -> None:
        if self._graph.has_edge(source, target):
            self._graph.edges[source, target]["health"] = health

    def to_snapshot_json(self) -> dict[str, Any]:
        nodes = [{"id": n, **self._graph.nodes[n]} for n in self._graph.nodes]
        edges = [
            {"source": u, "target": v, **self._graph.edges[u, v]}
            for u, v in self._graph.edges
        ]
        return {"nodes": nodes, "edges": edges, "generated_at": datetime.utcnow().isoformat()}

    def diff_snapshots(self, previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
        prev_nodes = {n["id"] for n in previous.get("nodes", [])}
        curr_nodes = {n["id"] for n in current.get("nodes", [])}
        prev_edges = {(e["source"], e["target"]) for e in previous.get("edges", [])}
        curr_edges = {(e["source"], e["target"]) for e in current.get("edges", [])}
        return {
            "added_nodes": list(curr_nodes - prev_nodes),
            "removed_nodes": list(prev_nodes - curr_nodes),
            "added_edges": [f"{s}->{t}" for s, t in curr_edges - prev_edges],
            "removed_edges": [f"{s}->{t}" for s, t in prev_edges - curr_edges],
        }

    def to_topology_event(self, cluster_id: str) -> TopologyEvent:
        snapshot = self.to_snapshot_json()
        return TopologyEvent(
            event_id=uuid4(),
            source="dependency-engine",
            cluster_id=cluster_id,
            namespace="*",
            payload={
                "node_count": len(snapshot["nodes"]),
                "edge_count": len(snapshot["edges"]),
                "graph": snapshot,
            },
        )

    def _is_critical_service(self, node_id: str) -> bool:
        """Check if a node is a critical infrastructure service."""
        name = node_id.split("/")[-1].lower()
        return any(critical in name for critical in self.CRITICAL_SERVICES)

    def _compute_propagated_health(self, source_health: str, influence: float) -> str:
        """Compute health status based on propagation influence."""
        if source_health == "critical":
            if influence > 0.7:
                return "critical"
            elif influence > 0.4:
                return "warning"
            else:
                return "unknown"
        elif source_health == "warning":
            if influence > 0.6:
                return "warning"
            else:
                return "unknown"
        return "unknown"
