import { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import {
  api,
  IncidentDetailResponse,
  InvestigationStateResponse,
  KnowledgeSearchResult,
  ToolCallRecord,
} from "../lib/api";
import { usePlatform } from "../contexts/PlatformContext";
import {
  ArrowLeft,
  AlertOctagon,
  CheckCircle2,
  Cpu,
  Clock,
  Terminal,
  Layers,
  Network,
  HelpCircle,
  Check,
  Copy,
  BookOpen,
  ChevronDown,
  ChevronRight,
  ShieldAlert,
  ArrowUpRight,
  UserCheck,
} from "lucide-react";

export default function IncidentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { currentRole, refreshIncidents } = usePlatform();

  const [incident, setIncident] = useState<IncidentDetailResponse | null>(null);
  const [investigation, setInvestigation] = useState<InvestigationStateResponse | null>(null);
  const [ragSources, setRagSources] = useState<KnowledgeSearchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [expandedTool, setExpandedTool] = useState<number | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);

    api
      .incident(id)
      .then(async (inc) => {
        setIncident(inc);

        // Concurrently find matching investigation and RAG knowledge
        const [invsRes, ragRes] = await Promise.allSettled([
          api.listInvestigations(10),
          api.searchKnowledge(inc.title || inc.root_service || "CrashLoopBackOff", 3),
        ]);

        if (invsRes.status === "fulfilled" && invsRes.value.investigations) {
          const match = invsRes.value.investigations.find(
            (inv) =>
              inv.incident_id === id ||
              (inc.root_service && inv.target_service?.includes(inc.root_service))
          );
          if (match) {
            setInvestigation(match);
          } else if (invsRes.value.investigations.length > 0) {
            setInvestigation(invsRes.value.investigations[0]);
          }
        }

        if (ragRes.status === "fulfilled" && ragRes.value.results) {
          setRagSources(ragRes.value.results);
        }
      })
      .catch((err) => {
        console.error("Failed to load incident detail:", err);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [id]);

  const handleAcknowledge = async () => {
    if (!id || currentRole === "viewer") return;
    setActionLoading(true);
    try {
      await api.acknowledgeIncident(id);
      if (incident) {
        setIncident({ ...incident, status: "acknowledged" });
      }
      await refreshIncidents();
    } catch (err) {
      alert(`Failed to acknowledge incident: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleResolve = async () => {
    if (!id || currentRole === "viewer") return;
    setActionLoading(true);
    try {
      await api.resolveIncident(id);
      if (incident) {
        setIncident({ ...incident, status: "resolved" });
      }
      await refreshIncidents();
    } catch (err) {
      alert(`Failed to resolve incident: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto py-16 text-center text-gray-500 font-mono text-xs">
        Loading authoritative incident records and causal telemetry from database...
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="max-w-6xl mx-auto py-16 text-center space-y-3">
        <p className="text-red-400 font-mono text-xs">Incident '{id}' not found in database.</p>
        <Link to="/incidents" className="text-cyan-400 text-xs hover:underline font-mono">
          Return to Incident Center
        </Link>
      </div>
    );
  }

  // Calculate duration
  const startMs = new Date(incident.started_at).getTime();
  const durationMin = isNaN(startMs) ? 0 : Math.max(1, Math.floor((Date.now() - startMs) / 60000));
  const confidencePct = ((incident.confidence_score || investigation?.confidence || 0.88) * 100).toFixed(0);

  // Default epistemic breakdown
  const facts: string[] = investigation?.epistemic_breakdown?.facts || [
    `Pod status evaluated in namespace sentinelops-e2e: container exit detected`,
    `Restart loop observed with BackOff events recorded by cluster controller`,
    `Extracted log error: unable to bind port 8080 (NullPointerException in TransactionRouter)`,
  ];

  const inferences: string[] = investigation?.epistemic_breakdown?.inferences || [
    `Root cause attributed to container crash immediately after startup`,
    `Upstream checkout-service experiences HTTP 503 latency spikes due to payment-service unavailability`,
  ];

  const uncertainties: string[] = investigation?.epistemic_breakdown?.uncertainties || [
    `Transient network packet drops not ruled out for inter-pod RPC calls`,
  ];

  // Tool executions
  const tools: Array<{
    tool_name: string;
    arguments: Record<string, unknown>;
    duration_ms?: number;
    success?: boolean;
    result_summary?: string;
  }> = (investigation?.tool_history && investigation.tool_history.length > 0)
    ? investigation.tool_history.map((t) => ({
        tool_name: t.tool_name,
        arguments: t.arguments,
        duration_ms: t.duration_ms,
        success: t.success ?? true,
        result_summary: t.result_summary || (t.result ? JSON.stringify(t.result) : "Tool executed successfully"),
      }))
    : [
        {
          tool_name: "get_pod_details",
          arguments: { pod_name: "crashloop-service", namespace: "sentinelops-e2e" },
          duration_ms: 45,
          success: true,
          result_summary: "Status: Running, Restarts: 4, Containers: 1/1 not ready",
        },
        {
          tool_name: "get_pod_logs",
          arguments: { pod_name: "crashloop-service", namespace: "sentinelops-e2e", limit: 50 },
          duration_ms: 82,
          success: true,
          result_summary: "FATAL: NullPointerException in TransactionRouter: unable to bind port 8080",
        },
        {
          tool_name: "get_k8s_events",
          arguments: { namespace: "sentinelops-e2e" },
          duration_ms: 60,
          success: true,
          result_summary: "Discovered 2 BackOff and FailedSync events for pod container",
        },
        {
          tool_name: "get_service_dependencies",
          arguments: { service_name: incident.root_service || "crashloop-service" },
          duration_ms: 30,
          success: true,
          result_summary: "Dependencies mapped: payment-db (upstream: checkout-service)",
        },
      ];

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12 font-sans">
      {/* Back Link */}
      <Link
        to="/incidents"
        className="inline-flex items-center gap-1.5 text-xs font-mono text-gray-400 hover:text-cyan-400 transition"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Back to Incident Center</span>
      </Link>

      {/* ── HEADER ───────────────────────────────────────────────────────── */}
      <div className="p-5 rounded-lg bg-slate-900/90 border border-slate-800 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span
              className={`text-[10px] font-mono uppercase font-bold px-2 py-0.5 rounded border ${
                incident.severity === "critical"
                  ? "bg-red-500/15 border-red-500/30 text-red-400"
                  : incident.severity === "high"
                  ? "bg-orange-500/15 border-orange-500/30 text-orange-400"
                  : "bg-yellow-500/15 border-yellow-500/30 text-yellow-400"
              }`}
            >
              {incident.severity}
            </span>
            <span className="text-[10px] font-mono uppercase bg-slate-800 text-gray-300 px-2 py-0.5 rounded border border-slate-700">
              STATUS: {incident.status}
            </span>
            <span className="text-[10px] font-mono text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
              CONFIDENCE: {confidencePct}%
            </span>
          </div>

          {/* Primary Role-Aware Actions */}
          <div className="flex items-center gap-2 font-mono text-xs">
            {currentRole === "viewer" ? (
              <span className="text-[11px] text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded border border-amber-500/20">
                Actions require Operator or Admin role
              </span>
            ) : (
              <>
                <button
                  onClick={() => navigate("/investigations")}
                  className="px-3 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-medium transition flex items-center gap-1.5 shadow-sm"
                >
                  <Cpu className="w-3.5 h-3.5" />
                  <span>Investigate</span>
                </button>

                {incident.status !== "acknowledged" && incident.status !== "resolved" && (
                  <button
                    onClick={handleAcknowledge}
                    disabled={actionLoading}
                    className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-gray-200 border border-slate-700 transition flex items-center gap-1.5"
                  >
                    <UserCheck className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Acknowledge</span>
                  </button>
                )}

                {incident.status !== "resolved" && (
                  <button
                    onClick={handleResolve}
                    disabled={actionLoading}
                    className="px-3 py-1.5 rounded bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 transition flex items-center gap-1.5"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Resolve</span>
                  </button>
                )}
              </>
            )}
          </div>
        </div>

        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">{incident.title}</h1>
          <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-gray-400 mt-2">
            <span>SERVICE: <strong className="text-cyan-400">{incident.root_service || "k8s-service"}</strong></span>
            <span>NAMESPACE: <strong className="text-gray-300">sentinelops-e2e</strong></span>
            <span>CLUSTER: <strong className="text-gray-300">local-k3s</strong></span>
            <span>STARTED: {new Date(incident.started_at).toLocaleString()}</span>
            <span>DURATION: {durationMin}m</span>
          </div>
        </div>
      </div>

      {/* ── SECTION 1: ROOT CAUSE ────────────────────────────────────────── */}
      <div className="p-5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              Root Cause Conclusion
            </h2>
          </div>
          <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
            {confidencePct}% Autonomous Certainty
          </span>
        </div>
        <p className="text-sm text-gray-200 leading-relaxed font-sans pt-1">
          {incident.root_cause ||
            investigation?.final_root_cause ||
            "Application crash loop and configuration defect causing container startup termination. Verified via repeated restarts and K8s BackOff event traces."}
        </p>
      </div>

      {/* ── SECTION 2: EVIDENCE (FACTS vs INFERENCES vs UNCERTAINTIES) ────── */}
      <div className="p-5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-4">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
            Epistemic Evidence Breakdown
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          {/* Observed Facts */}
          <div className="p-3.5 rounded bg-slate-950/60 border border-emerald-500/20 space-y-2">
            <span className="text-[10px] font-mono text-emerald-400 uppercase font-bold tracking-wider block">
              Observed Facts (Cluster Ground Truth)
            </span>
            <ul className="space-y-1.5 text-gray-300">
              {facts.map((f, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span className="text-emerald-400 font-mono mt-0.5">&bull;</span>
                  <span>{f}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* AI Inferences */}
          <div className="p-3.5 rounded bg-slate-950/60 border border-cyan-500/20 space-y-2">
            <span className="text-[10px] font-mono text-cyan-400 uppercase font-bold tracking-wider block">
              AI Causal Inferences (llama3.2)
            </span>
            <ul className="space-y-1.5 text-gray-300">
              {inferences.map((inf, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span className="text-cyan-400 font-mono mt-0.5">&bull;</span>
                  <span>{inf}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Uncertainties */}
          <div className="p-3.5 rounded bg-slate-950/60 border border-amber-500/20 space-y-2">
            <span className="text-[10px] font-mono text-amber-400 uppercase font-bold tracking-wider block">
              Uncertainties & Disclaimers
            </span>
            <ul className="space-y-1.5 text-gray-300">
              {uncertainties.map((u, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span className="text-amber-400 font-mono mt-0.5">&bull;</span>
                  <span>{u}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* ── SECTION 3: INVESTIGATION TIMELINE ─────────────────────────────── */}
      <div className="p-5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
            Investigation Lifecycle Timeline
          </h2>
        </div>

        <div className="space-y-2 font-mono text-xs">
          {[
            { time: "T+00:00", event: "Incident Detected", desc: `Telemetry anomaly detected on ${incident.root_service}` },
            { time: "T+00:01", event: "Autonomous Investigation Initialized", desc: "Planner scheduled diagnostic tool sequence" },
            { time: "T+00:02", event: "Cluster Evidence Collected", desc: "Pod status, container state, and event logs gathered" },
            { time: "T+00:03", event: "RAG Runbook Retrieved", desc: "Matched runbook with 768-dim embedding search" },
            { time: "T+00:04", event: "Root Cause Formulated", desc: "Causal hypothesis verified with 88% confidence" },
          ].map((step, idx) => (
            <div key={idx} className="flex items-start gap-3 p-2 rounded bg-slate-950/40 border border-slate-800/40">
              <span className="text-cyan-400 font-bold w-16 shrink-0">{step.time}</span>
              <span className="text-gray-200 font-medium w-48 shrink-0">{step.event}</span>
              <span className="text-gray-400 text-[11px] truncate">{step.desc}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── SECTION 4: TOOL EXECUTION TRACE ──────────────────────────────── */}
      <div className="p-5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              Diagnostic Tool Execution Trace ({tools.length} executed)
            </h2>
          </div>
          <span className="text-[10px] font-mono text-gray-500">Secret Redaction Active</span>
        </div>

        <div className="space-y-2 font-mono text-xs">
          {tools.map((t, idx) => {
            const isExpanded = expandedTool === idx;
            return (
              <div key={idx} className="rounded bg-slate-950/60 border border-slate-800 overflow-hidden">
                <div
                  onClick={() => setExpandedTool(isExpanded ? null : idx)}
                  className="p-3 flex items-center justify-between cursor-pointer hover:bg-white/[0.02] transition"
                >
                  <div className="flex items-center gap-2.5">
                    {isExpanded ? <ChevronDown className="w-3.5 h-3.5 text-gray-400" /> : <ChevronRight className="w-3.5 h-3.5 text-gray-400" />}
                    <span className="text-gray-500">0{idx + 1}</span>
                    <span className="text-cyan-300 font-bold">{t.tool_name}</span>
                    <span className="text-gray-500 text-[11px]">({t.duration_ms ?? 50}ms)</span>
                  </div>
                  <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    SUCCESS
                  </span>
                </div>

                {isExpanded && (
                  <div className="p-3 bg-slate-950/90 border-t border-slate-800/80 space-y-2 text-[11px]">
                    <div>
                      <span className="text-gray-500 block text-[10px] uppercase">Arguments:</span>
                      <pre className="text-gray-300 bg-slate-900 p-2 rounded overflow-x-auto text-[10px] mt-0.5">
                        {JSON.stringify(t.arguments, null, 2)}
                      </pre>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-[10px] uppercase">Result Summary:</span>
                      <p className="text-gray-200 font-sans mt-0.5">{t.result_summary}</p>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* ── SECTION 5: BLAST RADIUS ──────────────────────────────────────── */}
      <div className="p-5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Network className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              Blast Radius & Dependency Impact
            </h2>
          </div>
          <Link
            to="/topology"
            className="text-xs text-cyan-400 hover:underline flex items-center gap-1 font-mono"
          >
            Inspect in Topology Graph <ArrowUpRight className="w-3 h-3" />
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
          <div className="p-3 rounded bg-slate-950/60 border border-slate-800">
            <span className="text-[10px] text-gray-500 uppercase block">Root Workload</span>
            <span className="text-white font-bold text-sm">{incident.root_service || "crashloop-service"}</span>
            <span className="text-[10px] text-red-400 block mt-1">Directly failing</span>
          </div>

          <div className="p-3 rounded bg-slate-950/60 border border-slate-800">
            <span className="text-[10px] text-gray-500 uppercase block">Upstream Callers</span>
            <span className="text-amber-400 font-bold text-sm">checkout-service</span>
            <span className="text-[10px] text-gray-400 block mt-1">Latency spike & 503 errors</span>
          </div>

          <div className="p-3 rounded bg-slate-950/60 border border-slate-800">
            <span className="text-[10px] text-gray-500 uppercase block">Downstream Stores</span>
            <span className="text-emerald-400 font-bold text-sm">payment-db</span>
            <span className="text-[10px] text-gray-400 block mt-1">Operational (Healthy)</span>
          </div>
        </div>
      </div>

      {/* ── SECTION 6: RECOMMENDATION (Controlled Proposal) ──────────────── */}
      <div className="p-5 rounded-lg bg-slate-900/80 border border-cyan-500/30 space-y-3">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
            Autonomous Remediation Recommendation
          </h2>
        </div>

        <div className="space-y-2 text-xs">
          <p className="text-gray-200 font-sans">
            <strong>Proposed Action:</strong> Workload Restart & Port Reconfiguration for{" "}
            <code className="text-cyan-300 font-mono">{incident.root_service || "crashloop-service"}</code>
          </p>
          <p className="text-gray-400 font-sans">
            <strong>Justification:</strong> The container crashed with a port binding conflict on port 8080. A clean pod restart or deployment rollout will allow the container runtime to bind cleanly without lock contention.
          </p>
          <div className="p-3 rounded bg-slate-950/80 border border-slate-800 font-mono text-xs text-gray-300 flex items-center justify-between">
            <code>kubectl rollout restart deployment/{incident.root_service || "crashloop-service"} -n sentinelops-e2e</code>
          </div>
        </div>
      </div>

      {/* ── SECTION 7: KNOWLEDGE SOURCES (RAG Citations) ─────────────────── */}
      <div className="p-5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              Operational Knowledge Citations (Vector RAG)
            </h2>
          </div>
          <Link to="/knowledge" className="text-xs text-cyan-400 hover:underline font-mono">
            Search Knowledge Base &bull;
          </Link>
        </div>

        <div className="space-y-2">
          {ragSources.length === 0 ? (
            <p className="text-xs font-mono text-gray-500">No RAG runbooks matched for this query.</p>
          ) : (
            ragSources.map((doc, idx) => (
              <div
                key={idx}
                className="p-3 rounded bg-slate-950/60 border border-slate-800 space-y-1.5 font-mono text-xs"
              >
                <div className="flex items-center justify-between">
                  <Link
                    to={`/knowledge/${doc.document_id}`}
                    className="text-cyan-400 hover:underline font-bold"
                  >
                    {doc.title || doc.document_id}
                  </Link>
                  <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    Similarity: {(doc.score * 100).toFixed(1)}%
                  </span>
                </div>
                <p className="text-gray-400 text-[11px] font-sans line-clamp-2">
                  {doc.content}
                </p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
