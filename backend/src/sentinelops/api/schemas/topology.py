from pydantic import BaseModel


class TopologyNode(BaseModel):
    id: str
    namespace: str | None = None
    kind: str | None = None
    name: str | None = None


class TopologyEdge(BaseModel):
    source: str
    target: str
    edge_type: str | None = None
    confidence: float | None = None


class TopologyGraphResponse(BaseModel):
    nodes: list[TopologyNode]
    edges: list[TopologyEdge]
    node_count: int
    edge_count: int
