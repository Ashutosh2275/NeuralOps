const API_BASE = import.meta.env.VITE_API_URL || "";

export type Role = "viewer" | "operator" | "admin";

export interface SessionInfo {
  user_id: string;
  username: string;
  role: Role;
  is_active: boolean;
}

const ROLE_STORAGE_KEY = "sentinelops_active_role";

export function getActiveRole(): Role {
  if (typeof window === "undefined" || !window.localStorage) return "operator";
  const stored = localStorage.getItem(ROLE_STORAGE_KEY);
  if (stored === "viewer" || stored === "operator" || stored === "admin") {
    return stored;
  }
  return "operator";
}

export function setActiveRole(role: Role): void {
  if (typeof window !== "undefined" && window.localStorage) {
    localStorage.setItem(ROLE_STORAGE_KEY, role);
    window.dispatchEvent(new CustomEvent("sentinelops-role-change", { detail: role }));
  }
}

export function getApiKeyForRole(role: Role): string {
  return `sentinelops-${role}-secret-key`;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const currentRole = getActiveRole();
  const apiKey = getApiKeyForRole(currentRole);

  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": apiKey,
      ...options?.headers,
    },
    ...options,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json();
}

// ── Models ─────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: "HEALTHY" | "DEGRADED" | "UNAVAILABLE";
  version: string;
  dependencies: Record<string, "healthy" | "degraded" | "unavailable">;
  healthy_count: number;
  total_dependencies: number;
  features: Record<string, boolean>;
  timestamp?: string;
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

export interface IncidentDetailResponse {
  id: string;
  title: string;
  status: string;
  severity: string;
  root_service: string | null;
  confidence_score: number | null;
  started_at: string;
  root_cause: string | null;
  affected_services: string[];
  cascade_chain: Array<Record<string, unknown>>;
  timeline: Array<{ timestamp: string; title: string; type: string }>;
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

export interface InvestigationEvidence {
  id: string;
  evidence_type: string;
  source_tool: string;
  summary: string;
  confidence_contribution: number;
  raw_data?: unknown;
}

export interface InvestigationHypothesis {
  hypothesis_id: string;
  description: string;
  status: string;
  confidence: number;
  reasoning: string;
  refuting_evidence_ids?: string[];
}

export interface ToolCallRecord {
  call_id: string;
  tool_name: string;
  arguments: Record<string, unknown>;
  result?: {
    success: boolean;
    data: unknown;
    errors: string[];
  };
  duration_ms: number;
  latency_ms?: number;
  timestamp: string;
  success?: boolean;
  result_summary?: string;
}

export interface InvestigationStateResponse {
  investigation_id: string;
  incident_id?: string;
  target_service?: string;
  target_pod?: string;
  namespace: string;
  initial_trigger: string;
  trigger_reason?: string;
  status: string;
  step_count: number;
  max_steps: number;
  evidence: InvestigationEvidence[];
  hypotheses: InvestigationHypothesis[];
  tool_history?: ToolCallRecord[];
  final_root_cause?: string;
  final_recommendations: string[];
  confidence: number;
  created_at: string;
  epistemic_breakdown?: {
    facts?: string[];
    inferences?: string[];
    uncertainties?: string[];
  };
}

export interface ToolMetadata {
  name: string;
  description: string;
  category: string;
  permission: string;
  parameters?: Record<string, unknown>;
  required_params?: string[];
  timeout_seconds?: number;
}

export interface PodInfo {
  pod_name: string;
  namespace: string;
  phase: string;
  ready: boolean;
  reason?: string;
  status_display?: string;
  restart_count: number;
  node_name?: string;
  start_time?: string;
  ip_address?: string;
  pod_ip?: string;
  labels?: Record<string, string>;
  containers?: Array<{
    name: string;
    ready: boolean;
    restart_count: number;
    image: string;
    state: string;
  }>;
}

export interface WorkloadsOverview {
  namespace: string;
  total_pods: number;
  running_pods: number;
  failing_pods: number;
  total_deployments: number;
  total_restarts: number;
  status: "HEALTHY" | "CRITICAL" | "WARNING";
}

export interface KnowledgeDocument {
  document_id: string;
  title: string;
  provider_type: string;
  chunk_count: number;
  status: string;
}

export interface KnowledgeChunk {
  chunk_id: string;
  title: string;
  provider_type: string;
  section: string;
  content: string;
  metadata?: Record<string, unknown>;
}

export interface KnowledgeDocumentDetail {
  document_id: string;
  title: string;
  provider_type: string;
  chunk_count: number;
  full_content: string;
  chunks: KnowledgeChunk[];
}

export interface PodDetailResponse {
  pod: PodInfo;
  logs: Array<{ timestamp: string; log_line: string; pod_name?: string }>;
  metrics: Array<{ metric_name: string; value: number; metric_unit: string; pod_name?: string }>;
}

export interface KnowledgeSearchResult {
  chunk_id: string;
  document_id: string;
  title: string;
  section: string;
  content: string;
  score: number;
  metadata?: Record<string, unknown>;
}

export interface AuditEvent {
  event_id: string;
  timestamp: string;
  actor: string;
  role?: string;
  actor_role?: string;
  action: string;
  request_path?: string;
  resource?: string;
  target_resource?: string;
  investigation_id?: string;
  selected_tools?: string[];
  sanitized_arguments?: Record<string, unknown>;
  execution_status?: string;
  duration_ms?: number;
  evidence_sources?: string[];
  citations?: string[];
  confidence?: number;
  final_rca?: string;
  warnings?: string[];
  errors?: string[];
  details?: Record<string, unknown>;
}

export interface SystemInfo {
  platform: {
    name: string;
    version: string;
    environment: string;
    cluster_id: string;
    namespace: string;
  };
  ai_engine: {
    provider: string;
    llm_model: string;
    embedding_model: string;
    context_length: number;
    gpu_acceleration: string;
    temperature: number;
  };
  infrastructure: {
    kubernetes_endpoint: string;
    prometheus_url: string;
    loki_url: string;
    redis_host: string;
    postgres_host: string;
    vector_store_path: string;
  };
  governance: {
    autonomous_mode: boolean;
    zero_trust_enclave: boolean;
    human_approval_required_for_remediation: boolean;
    audit_trail_enabled: boolean;
    rbac_roles: string[];
  };
}

// ── Central API Client ──────────────────────────────────────────────────

export const api = {
  // System Health
  health: () => request<HealthResponse>("/api/v1/health"),
  systemInfo: () => request<SystemInfo>("/api/v1/system/info"),

  // Incidents
  incidents: () => request<IncidentSummary[]>("/api/v1/incidents"),
  incident: (id: string) => request<IncidentDetailResponse>(`/api/v1/incidents/${id}`),
  replay: (id: string) =>
    request<{ timeline: unknown[]; frames: unknown[] }>(`/api/v1/incidents/${id}/replay`),
  rca: (id: string) => request<Record<string, unknown>>(`/api/v1/intelligence/incidents/${id}/rca`),
  recommendations: (id: string) =>
    request<Recommendation[]>(`/api/v1/intelligence/incidents/${id}/recommendations`),
  insights: (id: string) => request<AIInsight[]>(`/api/v1/intelligence/incidents/${id}/insights`),
  acknowledgeIncident: (id: string) =>
    request<{ id: string; status: string }>(`/api/v1/incidents/${id}/acknowledge`, { method: "POST" }),
  resolveIncident: (id: string) =>
    request<{ id: string; status: string }>(`/api/v1/incidents/${id}/resolve`, { method: "POST" }),

  // Investigations
  startInvestigation: (params: {
    incident_id?: string;
    service_name?: string;
    pod_name?: string;
    namespace?: string;
    trigger_reason?: string;
    max_steps?: number;
  }) =>
    request<{ status: string; investigation: InvestigationStateResponse }>("/api/v1/investigations", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  getInvestigation: (id: string) =>
    request<{ investigation: InvestigationStateResponse }>(`/api/v1/investigations/${id}`),
  listInvestigations: (limit?: number) =>
    request<{ count: number; investigations: InvestigationStateResponse[] }>(
      `/api/v1/investigations${limit ? `?limit=${limit}` : ""}`
    ),

  // Topology
  topology: () => request<TopologyGraph>("/api/v1/topology/graph"),
  blastRadius: (ns: string, pod: string) =>
    request<Record<string, unknown>>(`/api/v1/intelligence/blast-radius/${ns}/${pod}`),

  // Workloads
  workloadsOverview: (ns?: string) =>
    request<WorkloadsOverview>(`/api/v1/workloads/overview${ns ? `?namespace=${ns}` : ""}`),
  workloadPods: (ns?: string) =>
    request<{ namespace: string; count: number; pods: PodInfo[] }>(
      `/api/v1/workloads/pods${ns ? `?namespace=${ns}` : ""}`
    ),
  workloadDeployments: (ns?: string) =>
    request<{ namespace: string; count: number; deployments: Array<Record<string, unknown>> }>(
      `/api/v1/workloads/deployments${ns ? `?namespace=${ns}` : ""}`
    ),
  workloadLogs: (podName?: string, ns?: string, limit?: number) =>
    request<{ namespace: string; count: number; logs: Array<{ timestamp: string; log_line: string; pod_name: string }> }>(
      `/api/v1/workloads/logs?${podName ? `pod_name=${podName}&` : ""}${ns ? `namespace=${ns}&` : ""}limit=${limit || 50}`
    ),
  workloadMetrics: (podName?: string, ns?: string) =>
    request<{ namespace: string; count: number; metrics: Array<{ metric_name: string; value: number; metric_unit: string; pod_name?: string }> }>(
      `/api/v1/workloads/metrics?${podName ? `pod_name=${podName}&` : ""}${ns ? `namespace=${ns}` : ""}`
    ),
  workloadPodDetail: (namespace: string, podName: string) =>
    request<PodDetailResponse>(`/api/v1/workloads/pods/${namespace}/${podName}`),

  // Knowledge & RAG
  knowledgeDocuments: () =>
    request<{ count: number; total_chunks: number; documents: KnowledgeDocument[] }>(
      "/api/v1/knowledge/documents"
    ),
  knowledgeDocument: (documentId: string) =>
    request<KnowledgeDocumentDetail>(`/api/v1/knowledge/documents/${documentId}`),
  searchKnowledge: (query: string, top_k?: number) =>
    request<{ query: string; count: number; results: KnowledgeSearchResult[] }>(
      "/api/v1/knowledge/search",
      {
        method: "POST",
        body: JSON.stringify({ query, top_k: top_k || 4 }),
      }
    ),

  // Tools & Audit
  listTools: () => request<{ count: number; tools: ToolMetadata[] }>("/api/v1/investigations/tools"),
  executeTool: (toolName: string, args: Record<string, unknown>) =>
    request<{ call_record: ToolCallRecord }>(`/api/v1/investigations/tools/${toolName}/execute`, {
      method: "POST",
      body: JSON.stringify(args),
    }),
  auditEvents: (limit?: number) =>
    request<{ count: number; events: AuditEvent[] }>(
      `/api/v1/investigations/audit/events${limit ? `?limit=${limit}` : ""}`
    ),

  // Natural Language Oracle
  nlpQuery: (question: string, namespace?: string) =>
    request<{ answer: string; intent?: string }>("/api/v1/nlp/query", {
      method: "POST",
      body: JSON.stringify({ question, namespace }),
    }),

  // Scenario trigger
  triggerScenario: (scenario: string) =>
    request<{ incident_count: number; simulation_ids: string[]; status: string }>("/api/v1/scenarios/trigger", {
      method: "POST",
      body: JSON.stringify({ scenario }),
    }),

  // Session & RBAC Auth
  session: () => request<SessionInfo>("/api/v1/system/session"),

  // Data Retention Policy Execution (Admin only)
  retentionCleanup: (dryRun: boolean = true) =>
    request<{
      dry_run: boolean;
      investigations: { scanned: number; expired: number; deleted: number; details: string[] };
      audit_trail: { scanned: number; expired: number; deleted: number; details: string[] };
    }>(`/api/v1/investigations/retention/cleanup?dry_run=${dryRun}`, {
      method: "POST",
    }),
};
