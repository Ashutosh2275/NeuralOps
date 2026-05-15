const API_BASE = import.meta.env.VITE_API_URL || "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json();
}

export interface IncidentSummary {
  id: string;
  title: string;
  status: string;
  severity: string;
  root_service: string | null;
  confidence_score: number | null;
  started_at: string;
}

export interface TopologyNode {
  id: string;
  namespace?: string;
  kind?: string;
  name?: string;
  health?: string;
  labels?: Record<string, string>;
}

export interface TopologyEdge {
  source: string;
  target: string;
  edge_type?: string;
  confidence?: number;
  health?: string;
}

export interface TopologyGraph {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
  node_count: number;
  edge_count: number;
}

export interface Recommendation {
  id: string;
  title: string;
  description: string;
  action_type: string;
  kubectl_command: string | null;
  priority: number;
  confidence: number;
}

export interface AIInsight {
  agent: string;
  title: string;
  content: string;
  confidence: number;
}

export interface CascadingFailure {
  cascade: {
    origin: string;
    chain: Array<{
      service: string;
      order: number;
      failure_mode: string;
      influence: number;
    }>;
    affected_count: number;
    propagation_depth: number;
    escalation_factor: number;
  };
  health_propagations: Array<{
    node: string;
    original: string;
    propagated: string;
    influence: number;
    path_length: number;
  }>;
}

export const api = {
  health: () => request<{ status: string; services: Record<string, boolean> }>("/api/v1/health"),
  incidents: () => request<IncidentSummary[]>("/api/v1/incidents"),
  incident: (id: string) => request<Record<string, unknown>>(`/api/v1/incidents/${id}`),
  replay: (id: string) =>
    request<{ timeline: unknown[]; frames: unknown[] }>(`/api/v1/incidents/${id}/replay`),
  topology: () => request<TopologyGraph>("/api/v1/topology/graph"),
  topologyVersions: (limit?: number) =>
    request<{ version: number; node_count: number; edge_count: number }[]>(
      `/api/v1/topology/versions${limit ? `?limit=${limit}` : ""}`
    ),
  rca: (id: string) => request<Record<string, unknown>>(`/api/v1/intelligence/incidents/${id}/rca`),
  recommendations: (id: string) => request<Recommendation[]>(`/api/v1/intelligence/incidents/${id}/recommendations`),
  insights: (id: string) => request<AIInsight[]>(`/api/v1/intelligence/incidents/${id}/insights`),
  blastRadius: (ns: string, pod: string) =>
    request<Record<string, unknown>>(`/api/v1/topology/blast-radius/${ns}/${pod}`),
  cascadingFailure: (ns: string, pod: string) =>
    request<CascadingFailure>(`/api/v1/topology/cascade/${ns}/${pod}`),
  healthPropagation: (ns: string, pod: string) =>
    request<Record<string, unknown>>(`/api/v1/topology/health-propagation/${ns}/${pod}`),
  nlpQuery: (question: string, namespace?: string) =>
    request<{ answer: string; intent?: string }>("/api/v1/nlp/query", {
      method: "POST",
      body: JSON.stringify({ question, namespace }),
    }),
  ingestionStatus: () => request<{ streams: Record<string, number> }>("/api/v1/ingestion/status"),
  triggerIngestion: () => request<{ published: number }>("/api/v1/ingestion/trigger", { method: "POST" }),
};
