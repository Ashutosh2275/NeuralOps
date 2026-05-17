"""
WebSocket Optimizer — System 13
Delta compression, event deduplication, per-client subscription filters.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

# Track last-sent hash per connection to skip identical payloads
_last_hash: dict[int, str] = {}


def deduplicate(conn_id: int, event_type: str, payload: dict) -> bool:
    """Returns True if this message should be sent (not a duplicate)."""
    key = json.dumps({"t": event_type, "p": payload}, sort_keys=True, default=str)
    h = hashlib.md5(key.encode()).hexdigest()
    if _last_hash.get(conn_id) == h:
        return False
    _last_hash[conn_id] = h
    return True


def clear_conn(conn_id: int) -> None:
    _last_hash.pop(conn_id, None)


def compress_topology(nodes: list[dict], edges: list[dict]) -> dict:
    """
    Returns only node IDs + health fields to minimise WS payload.
    Full node data is fetched on demand by the frontend.
    """
    return {
        "nodes": [{"id": n.get("id"), "h": n.get("health", "healthy")} for n in nodes],
        "edges": [{"s": e.get("source"), "t": e.get("target"), "h": e.get("health", "healthy")} for e in edges],
    }


def build_delta(prev: dict, curr: dict) -> dict:
    """
    Returns only the keys that changed between two topology snapshots.
    Frontend merges deltas into local state.
    """
    delta: dict[str, Any] = {}
    prev_nodes = {n["id"]: n for n in prev.get("nodes", [])}
    curr_nodes = {n["id"]: n for n in curr.get("nodes", [])}

    changed_nodes = []
    for nid, node in curr_nodes.items():
        if prev_nodes.get(nid) != node:
            changed_nodes.append(node)

    removed_nodes = [nid for nid in prev_nodes if nid not in curr_nodes]

    if changed_nodes:
        delta["changed_nodes"] = changed_nodes
    if removed_nodes:
        delta["removed_nodes"] = removed_nodes

    return delta
