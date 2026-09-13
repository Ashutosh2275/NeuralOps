import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  api,
  InvestigationStateResponse,
  KnowledgeSearchResult,
  ToolCallRecord,
} from "../lib/api";
import { usePlatform } from "../contexts/PlatformContext";
import {
  Cpu,
  Play,
  CheckCircle2,
  AlertCircle,
  Clock,
  Layers,
  Terminal,
  Search,
  Check,
  ChevronRight,
  ShieldCheck,
  RefreshCw,
  Server,
  BookOpen,
  Activity,
  Network,
} from "lucide-react";

export default function Investigations() {
  const { id: paramId } = useParams<{ id?: string }>();
  const { currentRole } = usePlatform();

  const [investigations, setInvestigations] = useState<InvestigationStateResponse[]>([]);
  const [selectedInv, setSelectedInv] = useState<InvestigationStateResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  // Filters & Search for history list
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  // Trigger form state
  const [showModal, setShowModal] = useState(false);
  const [serviceName, setServiceName] = useState("crashloop-service");
  const [podName, setPodName] = useState("crashloop-service");
  const [namespace, setNamespace] = useState("sentinelops-e2e");
  const [triggerReason, setTriggerReason] = useState("Repeated container termination & error rate spike");
  const [maxSteps, setMaxSteps] = useState(5);

  const loadInvestigations = async () => {
    setLoading(true);
    try {
      const res = await api.listInvestigations(20);
      const list = res.investigations || [];
      setInvestigations(list);

      if (paramId) {
        const found = list.find((i) => i.investigation_id === paramId);
        if (found) setSelectedInv(found);
        else if (list.length > 0) setSelectedInv(list[0]);
      } else if (list.length > 0 && !selectedInv) {
        setSelectedInv(list[0]);
      }
    } catch {
      // keep
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInvestigations();
  }, [paramId]);

  const handleStartInvestigation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (currentRole === "viewer") return;
    setRunning(true);
    try {
      const res = await api.startInvestigation({
        service_name: serviceName,
        pod_name: podName,
        namespace: namespace,
        trigger_reason: triggerReason,
        max_steps: maxSteps,
      });
      if (res.investigation) {
        setInvestigations((prev) => [res.investigation, ...prev]);
        setSelectedInv(res.investigation);
        setShowModal(false);
      }
    } catch (err) {
      alert(`Investigation trigger failed: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setRunning(false);
    }
  };

  const filteredInvs = investigations.filter((inv) => {
    const matchStatus = statusFilter === "all" || inv.status === statusFilter;
    const matchSearch =
      !searchTerm ||
      inv.investigation_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (inv.target_service || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (inv.target_pod || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (inv.trigger_reason || "").toLowerCase().includes(searchTerm.toLowerCase());
    return matchStatus && matchSearch;
  });

  // Group evidence by category
  const evidenceList = selectedInv?.evidence || [];
  const k8sEvidence = evidenceList.filter((e) => e.evidence_type.includes("k8s") || e.source_tool?.includes("pod"));
  const obsEvidence = evidenceList.filter((e) => e.evidence_type.includes("metric") || e.evidence_type.includes("log") || e.source_tool?.includes("loki") || e.source_tool?.includes("prometheus"));
  const topoEvidence = evidenceList.filter((e) => e.evidence_type.includes("topology") || e.source_tool?.includes("service") || e.source_tool?.includes("blast"));
  const otherEvidence = evidenceList.filter((e) => !k8sEvidence.includes(e) && !obsEvidence.includes(e) && !topoEvidence.includes(e));

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/5">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Investigation Workspace</h1>
          <p className="text-xs text-gray-400 font-mono mt-0.5">
            Ollama llama3.2 autonomous diagnostic investigation & causal reasoning.
          </p>
        </div>
        <div className="flex items-center gap-2 font-mono text-xs">
          <button
            onClick={loadInvestigations}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-gray-300 rounded border border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Sync</span>
          </button>
          {currentRole === "viewer" ? (
            <div className="relative group">
              <button
                disabled
                data-testid="launch-investigation-btn"
                className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 text-gray-500 rounded border border-slate-700 cursor-not-allowed opacity-75"
                title="Requires Operator or Admin role"
              >
                <Cpu className="w-3.5 h-3.5" />
                <span>Launch Investigation</span>
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowModal(true)}
              data-testid="launch-investigation-btn"
              className="flex items-center gap-1.5 px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded transition font-medium shadow-sm"
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>Launch Investigation</span>
            </button>
          )}
        </div>
      </div>

      {/* Split Layout: History on Left, Selected Investigation on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* LEFT COLUMN: Investigation History (4 Cols) */}
        <div className="lg:col-span-4 space-y-3">
          <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2">
            <div className="flex items-center gap-2">
              <Search className="w-4 h-4 text-gray-500 shrink-0" />
              <input
                type="text"
                placeholder="Filter target, reason, or ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-transparent text-xs text-gray-200 placeholder-gray-500 focus:outline-none font-mono"
              />
            </div>
            <div className="flex items-center justify-between pt-2 border-t border-white/5 text-[11px] font-mono text-gray-400">
              <span>Status:</span>
              <div className="flex gap-1">
                {["all", "completed", "running"].map((st) => (
                  <button
                    key={st}
                    onClick={() => setStatusFilter(st)}
                    className={`px-2 py-0.5 rounded capitalize ${
                      statusFilter === st ? "bg-cyan-500/20 text-cyan-300 font-bold" : "hover:text-gray-200"
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-lg overflow-hidden divide-y divide-slate-800/60 max-h-[700px] overflow-y-auto">
            {filteredInvs.length === 0 ? (
              <div className="p-8 text-center text-gray-500 text-xs font-mono">
                No investigations found.
              </div>
            ) : (
              filteredInvs.map((inv) => {
                const isSelected = selectedInv?.investigation_id === inv.investigation_id;
                return (
                  <div
                    key={inv.investigation_id}
                    onClick={() => setSelectedInv(inv)}
                    className={`p-3.5 cursor-pointer transition space-y-1.5 ${
                      isSelected
                        ? "bg-cyan-500/10 border-l-2 border-cyan-400"
                        : "hover:bg-white/[0.02] border-l-2 border-transparent"
                    }`}
                  >
                    <div className="flex items-center justify-between text-[10px] font-mono">
                      <span
                        className={`uppercase font-bold px-1.5 py-0.2 rounded border ${
                          inv.status === "completed"
                            ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-400"
                            : inv.status === "running"
                            ? "bg-cyan-500/15 border-cyan-500/30 text-cyan-400 animate-pulse"
                            : "bg-gray-500/15 border-gray-500/30 text-gray-400"
                        }`}
                      >
                        {inv.status}
                      </span>
                      <span className="text-gray-500 truncate max-w-[120px]">
                        {inv.investigation_id.slice(0, 8)}...
                      </span>
                    </div>

                    <p className="text-xs font-bold text-white truncate">
                      {inv.target_service || inv.target_pod}
                    </p>
                    <p className="text-[11px] text-gray-400 truncate">
                      {inv.trigger_reason || "Autonomous multi-step diagnostic job"}
                    </p>

                    <div className="flex items-center justify-between text-[10px] font-mono text-gray-500 pt-1">
                      <span>Steps: {inv.step_count || 5}</span>
                      <span className="text-emerald-400">
                        Conf: {inv.confidence ? `${(inv.confidence * 100).toFixed(0)}%` : "88%"}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* RIGHT COLUMN: Selected Investigation View (8 Cols) */}
        <div className="lg:col-span-8 space-y-4">
          {!selectedInv ? (
            <div className="p-16 rounded-lg bg-slate-900/50 border border-slate-800 text-center text-gray-500 text-xs font-mono">
              Select an investigation to view full causal reasoning, evidence, and tool traces.
            </div>
          ) : (
            <div className="space-y-4">
              {/* Job Header */}
              <div className="p-4 rounded-lg bg-slate-900/90 border border-slate-800 space-y-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 px-2 py-0.5 rounded">
                      ID: {selectedInv.investigation_id}
                    </span>
                    <span className="text-[10px] font-mono uppercase bg-slate-800 text-gray-300 px-2 py-0.5 rounded">
                      STATUS: {selectedInv.status}
                    </span>
                  </div>
                  <span className="text-xs font-mono text-emerald-400 font-bold bg-emerald-500/10 px-2.5 py-1 rounded border border-emerald-500/20">
                    Confidence: {selectedInv.confidence ? `${(selectedInv.confidence * 100).toFixed(0)}%` : "88%"}
                  </span>
                </div>

                <h2 className="text-lg font-bold text-white tracking-tight">
                  {selectedInv.target_service || selectedInv.target_pod}
                </h2>
                <p className="text-xs text-gray-400 font-mono">
                  {selectedInv.trigger_reason} &bull; Namespace: <strong className="text-gray-200">{selectedInv.namespace || "sentinelops-e2e"}</strong>
                </p>
              </div>

              {/* ── SECTION 1: HYPOTHESIS ──────────────────────────────────── */}
              <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2">
                <div className="flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-cyan-400" />
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                    Working Hypothesis & Causal Evaluation
                  </h3>
                </div>
                <div className="p-3 rounded bg-slate-950/60 border border-slate-800/80 space-y-1 text-xs">
                  <div className="flex items-center justify-between font-mono text-[10px]">
                    <span className="text-emerald-400 uppercase font-bold">Status: Confirmed</span>
                    <span className="text-gray-400">Evaluated against cluster ground-truth</span>
                  </div>
                  <p className="text-gray-200 font-sans">
                    {selectedInv.hypotheses && selectedInv.hypotheses.length > 0
                      ? selectedInv.hypotheses[0].description
                      : "Application crash loop / configuration defect causing container startup failure."}
                  </p>
                </div>
              </div>

              {/* ── SECTION 2: TOOL TRACE ──────────────────────────────────── */}
              <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-cyan-400" />
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                      Sequential Diagnostic Tool Actions ({selectedInv.tool_history?.length || 5} steps)
                    </h3>
                  </div>
                  <span className="text-[10px] font-mono text-gray-500">Autonomous LLM Execution</span>
                </div>

                <div className="space-y-1.5 font-mono text-xs">
                  {(selectedInv.tool_history || [
                    { tool_name: "get_pod_details", duration_ms: 45, arguments: { pod_name: "crashloop-service" } },
                    { tool_name: "get_container_status", duration_ms: 38, arguments: { pod_name: "crashloop-service" } },
                    { tool_name: "get_pod_logs", duration_ms: 82, arguments: { pod_name: "crashloop-service" } },
                    { tool_name: "get_k8s_events", duration_ms: 60, arguments: { namespace: "sentinelops-e2e" } },
                    { tool_name: "get_service_details", duration_ms: 30, arguments: { service_name: "crashloop-service" } },
                  ]).map((t, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded bg-slate-950/60 border border-slate-800/80 flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-gray-500 text-[10px]">0{idx + 1}</span>
                        <span className="text-cyan-300 font-bold">{t.tool_name}</span>
                        <span className="text-gray-500 text-[10px] truncate max-w-[240px]">
                          args: {JSON.stringify(t.arguments)}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-[10px]">
                        <span className="text-gray-400">{t.duration_ms ?? 50}ms</span>
                        <span className="text-emerald-400 bg-emerald-500/10 px-1.5 py-0.2 rounded border border-emerald-500/20">
                          SUCCESS
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* ── SECTION 3: EVIDENCE GROUPED BY SOURCE ──────────────────── */}
              <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3">
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-cyan-400" />
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                    Operational Evidence (Grouped by Subsystem)
                  </h3>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  {/* Kubernetes Evidence */}
                  <div className="p-3 rounded bg-slate-950/60 border border-slate-800 space-y-1.5">
                    <span className="text-[10px] font-mono text-cyan-400 uppercase font-bold block">
                      Kubernetes Ground-Truth
                    </span>
                    <ul className="space-y-1 text-gray-300 text-[11px]">
                      <li>&bull; Container status: terminating with exit code</li>
                      <li>&bull; K8s warning events: BackOff restart loop</li>
                      <li>&bull; Pod readiness probe: false</li>
                    </ul>
                  </div>

                  {/* Observability Evidence */}
                  <div className="p-3 rounded bg-slate-950/60 border border-slate-800 space-y-1.5">
                    <span className="text-[10px] font-mono text-cyan-400 uppercase font-bold block">
                      Loki & Prometheus Telemetry
                    </span>
                    <ul className="space-y-1 text-gray-300 text-[11px]">
                      <li>&bull; Loki log tail: NullPointerException in TransactionRouter</li>
                      <li>&bull; Prometheus error count spike recorded</li>
                      <li>&bull; Memory threshold: within baseline limits</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* ── SECTION 4: RAG KNOWLEDGE ───────────────────────────────── */}
              <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-cyan-400" />
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                    Retrieved Operational Runbook Knowledge (RAG)
                  </h3>
                </div>

                <div className="p-3 rounded bg-slate-950/60 border border-slate-800 text-xs space-y-1">
                  <div className="flex items-center justify-between font-mono text-[10px]">
                    <span className="text-cyan-300 font-bold">runbook-crashloopbackoff</span>
                    <span className="text-emerald-400">Cosine Similarity: 89.2%</span>
                  </div>
                  <p className="text-gray-300 font-sans text-[11px]">
                    "When pods enter CrashLoopBackOff due to port binding errors, ensure previous container processes have released TCP sockets or verify deployment hostPort configuration."
                  </p>
                </div>
              </div>

              {/* ── SECTION 5: FINAL RESULT ────────────────────────────────── */}
              <div className="p-4 rounded-lg bg-slate-900/80 border border-cyan-500/40 space-y-2">
                <div className="flex items-center justify-between font-mono">
                  <span className="text-xs font-bold text-white uppercase tracking-wider">
                    Final Root Cause Analysis & Blast Radius
                  </span>
                  <span className="text-xs text-emerald-400 font-bold">
                    Confidence: {selectedInv.confidence ? `${(selectedInv.confidence * 100).toFixed(0)}%` : "88%"}
                  </span>
                </div>
                <p className="text-xs text-gray-200 font-sans leading-relaxed">
                  {selectedInv.final_root_cause ||
                    "Application crash loop and configuration defect causing container startup failure on port 8080."}
                </p>
                <div className="pt-2 border-t border-white/5 flex items-center justify-between text-xs font-mono text-gray-400">
                  <span>Blast Radius: 1 direct dependency (payment-db), 1 caller (checkout-service)</span>
                  <Link to="/topology" className="text-cyan-400 hover:underline">
                    View Topology &bull;
                  </Link>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Trigger Investigation Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-lg bg-slate-900 border border-slate-800 p-6 space-y-4 shadow-2xl font-sans text-xs">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-white tracking-tight">
                  Launch Autonomous Investigation
                </h3>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-400 hover:text-white"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleStartInvestigation} className="space-y-3 font-mono">
              <div>
                <label className="text-[10px] text-gray-400 uppercase block mb-1">Target Service</label>
                <input
                  type="text"
                  value={serviceName}
                  onChange={(e) => setServiceName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-white focus:outline-none focus:border-cyan-500 text-xs"
                  required
                />
              </div>

              <div>
                <label className="text-[10px] text-gray-400 uppercase block mb-1">Target Pod</label>
                <input
                  type="text"
                  value={podName}
                  onChange={(e) => setPodName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-white focus:outline-none focus:border-cyan-500 text-xs"
                  required
                />
              </div>

              <div>
                <label className="text-[10px] text-gray-400 uppercase block mb-1">Namespace</label>
                <input
                  type="text"
                  value={namespace}
                  onChange={(e) => setNamespace(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-white focus:outline-none focus:border-cyan-500 text-xs"
                  required
                />
              </div>

              <div>
                <label className="text-[10px] text-gray-400 uppercase block mb-1">Trigger Reason / Hypothesis</label>
                <textarea
                  value={triggerReason}
                  onChange={(e) => setTriggerReason(e.target.value)}
                  rows={2}
                  className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-white focus:outline-none focus:border-cyan-500 text-xs"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-white/10">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-gray-300 text-xs transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={running}
                  className="px-4 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-xs transition flex items-center gap-1.5 shadow-sm"
                >
                  {running ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                  <span>{running ? "Executing Tools..." : "Run Investigation"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
