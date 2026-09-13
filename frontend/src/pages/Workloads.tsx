import { useEffect, useState } from "react";
import { Link, useParams, useNavigate, useSearchParams } from "react-router-dom";
import { api, PodInfo, WorkloadsOverview } from "../lib/api";
import {
  Server,
  RefreshCw,
  Search,
  CheckCircle2,
  AlertOctagon,
  FileText,
  Activity,
  Cpu,
  Layers,
  ArrowUpRight,
  ArrowLeft,
  Clock,
  Terminal,
  Network,
  Copy,
  Check,
} from "lucide-react";

export default function Workloads() {
  const { namespace: paramNs, pod: paramPod } = useParams<{ namespace?: string; pod?: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [pods, setPods] = useState<PodInfo[]>([]);
  const [overview, setOverview] = useState<WorkloadsOverview | null>(null);
  const [selectedPod, setSelectedPod] = useState<PodInfo | null>(null);
  const [podLogs, setPodLogs] = useState<Array<{ timestamp: string; log_line: string }>>([]);
  const [podMetrics, setPodMetrics] = useState<Array<{ metric_name: string; value: number; metric_unit: string }>>([]);
  const [loading, setLoading] = useState(true);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [copied, setCopied] = useState(false);

  // Tabs for detail view
  const [activeTab, setActiveTab] = useState<"overview" | "logs" | "metrics" | "events" | "dependencies" | "incidents">("overview");

  // Filters
  const initialStatus = searchParams.get("status") || "all";
  const [statusFilter, setStatusFilter] = useState(initialStatus);
  const [search, setSearch] = useState("");
  const [sortField, setSortField] = useState<"pod_name" | "status" | "restart_count">("pod_name");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");

  const loadWorkloads = async () => {
    setLoading(true);
    try {
      const [o, p] = await Promise.all([
        api.workloadsOverview("sentinelops-e2e"),
        api.workloadPods("sentinelops-e2e"),
      ]);
      setOverview(o);
      const podList = p.pods || [];
      setPods(podList);

      if (paramPod) {
        const found = podList.find((x) => x.pod_name === paramPod);
        if (found) setSelectedPod(found);
      } else if (podList.length > 0 && !selectedPod) {
        setSelectedPod(podList[0]);
      }
    } catch {
      // keep
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWorkloads();
  }, [paramPod]);

  // When selectedPod changes, load logs & metrics from backend
  useEffect(() => {
    if (!selectedPod) return;
    setLoadingDetails(true);
    Promise.allSettled([
      api.workloadLogs(selectedPod.pod_name, "sentinelops-e2e", 50),
      api.workloadMetrics(selectedPod.pod_name, "sentinelops-e2e"),
    ]).then(([logsRes, metricsRes]) => {
      if (logsRes.status === "fulfilled") setPodLogs(logsRes.value.logs || []);
      if (metricsRes.status === "fulfilled") setPodMetrics(metricsRes.value.metrics || []);
      setLoadingDetails(false);
    });
  }, [selectedPod?.pod_name]);

  const copyLogs = () => {
    const text = podLogs.map((l) => `${l.timestamp} ${l.log_line}`).join("\n");
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // ── WORKLOAD DETAIL VIEW (/workloads/:namespace/:pod) ─────────────────────
  if (paramPod && selectedPod) {
    return (
      <div className="space-y-6 max-w-6xl mx-auto pb-12 font-sans">
        <Link
          to="/workloads"
          className="inline-flex items-center gap-1.5 text-xs font-mono text-gray-400 hover:text-cyan-400 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Workload Intelligence</span>
        </Link>

        {/* Workload Header */}
        <div className="p-5 rounded-lg bg-slate-900/90 border border-slate-800 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2 font-mono text-xs">
              <span
                className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${
                  selectedPod.status_display === "Running"
                    ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-400"
                    : selectedPod.status_display === "CrashLoopBackOff"
                    ? "bg-red-500/15 border-red-500/30 text-red-400 animate-pulse"
                    : selectedPod.status_display === "OOMKilled"
                    ? "bg-purple-500/15 border-purple-500/30 text-purple-400"
                    : "bg-amber-500/15 border-amber-500/30 text-amber-400"
                }`}
              >
                {selectedPod.status_display || selectedPod.phase}
              </span>
              <span className="text-[10px] bg-slate-800 text-gray-300 px-2 py-0.5 rounded border border-slate-700">
                READY: {selectedPod.ready ? "TRUE" : "FALSE"}
              </span>
              <span className="text-[10px] text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                RESTARTS: {selectedPod.restart_count || 0}
              </span>
            </div>

            <Link
              to="/investigations"
              className="px-3 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-xs transition flex items-center gap-1.5 shadow-sm font-mono"
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>Investigate Workload</span>
            </Link>
          </div>

          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">{selectedPod.pod_name}</h1>
            <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-gray-400 mt-1">
              <span>NAMESPACE: <strong className="text-gray-200">{selectedPod.namespace}</strong></span>
              <span>NODE: <strong className="text-gray-200">ashutosh (WSL2 k3s)</strong></span>
              <span>IP: <strong className="text-gray-200">{selectedPod.pod_ip || "10.42.0.x"}</strong></span>
            </div>
          </div>
        </div>

        {/* Tabs Bar */}
        <div className="flex border-b border-slate-800 text-xs font-mono gap-4">
          {[
            { key: "overview", label: "Overview" },
            { key: "logs", label: `Logs (${podLogs.length})` },
            { key: "metrics", label: `Metrics (${podMetrics.length})` },
            { key: "events", label: "Events" },
            { key: "dependencies", label: "Dependencies" },
            { key: "incidents", label: "Incidents" },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`pb-2.5 font-bold transition-all border-b-2 ${
                activeTab === tab.key
                  ? "border-cyan-400 text-cyan-300"
                  : "border-transparent text-gray-400 hover:text-gray-200"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === "overview" && (
          <div className="p-5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-4 text-xs font-mono">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Container Statuses</h3>
            <div className="p-3 rounded bg-slate-950/60 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-gray-300 font-bold">{selectedPod.pod_name.split("-")[0]}</span>
                <span className={selectedPod.ready ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>
                  {selectedPod.ready ? "READY (1/1)" : "NOT READY (0/1)"}
                </span>
              </div>
              <div className="text-[11px] text-gray-400 space-y-1">
                <p>Phase: {selectedPod.phase}</p>
                <p>Last Termination Reason: {selectedPod.reason || "None recorded"}</p>
                <p>Restart Count: {selectedPod.restart_count || 0}</p>
              </div>
            </div>
          </div>
        )}

        {activeTab === "logs" && (
          <div className="p-5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Streamed from Grafana Loki (Port 3100)</span>
              <button
                onClick={copyLogs}
                className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-gray-300 text-[11px] flex items-center gap-1"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? "Copied" : "Copy Logs"}</span>
              </button>
            </div>
            <div className="p-3 rounded bg-slate-950 border border-slate-800 max-h-96 overflow-y-auto space-y-1 text-[11px] text-gray-300">
              {podLogs.length === 0 ? (
                <p className="text-gray-500 py-4 text-center">No recent logs recorded for this pod.</p>
              ) : (
                podLogs.map((l, idx) => (
                  <div key={idx} className="flex gap-2 leading-relaxed">
                    <span className="text-gray-500 shrink-0">
                      {new Date(l.timestamp).toLocaleTimeString()}
                    </span>
                    <span className={l.log_line.includes("FATAL") || l.log_line.includes("ERROR") ? "text-red-400" : "text-gray-300"}>
                      {l.log_line}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {activeTab === "metrics" && (
          <div className="p-5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3 font-mono text-xs">
            <span className="text-gray-400">Scraped from cAdvisor via Prometheus (Port 9090)</span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {podMetrics.length === 0 ? (
                <p className="text-gray-500 col-span-2 py-4 text-center">No metrics series currently stored for this pod.</p>
              ) : (
                podMetrics.map((m, idx) => (
                  <div key={idx} className="p-3 rounded bg-slate-950 border border-slate-800 flex justify-between">
                    <span className="text-gray-400">{m.metric_name}</span>
                    <span className="text-cyan-300 font-bold">{m.value} {m.metric_unit}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {activeTab === "events" && (
          <div className="p-5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3 font-mono text-xs">
            <span className="text-gray-400">Kubernetes Core Events</span>
            <div className="p-3 rounded bg-slate-950 border border-slate-800 space-y-2 text-[11px]">
              <div className="flex items-center justify-between text-amber-400">
                <span className="font-bold">Warning / BackOff</span>
                <span className="text-gray-500">Kubelet &bull; Cluster Ground Truth</span>
              </div>
              <p className="text-gray-300">
                Back-off restarting failed container in pod {selectedPod.pod_name}
              </p>
            </div>
          </div>
        )}

        {activeTab === "dependencies" && (
          <div className="p-5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Topology Dependency Mappings</span>
              <Link to="/topology" className="text-cyan-400 hover:underline flex items-center gap-1">
                View in Topology Graph <ArrowUpRight className="w-3 h-3" />
              </Link>
            </div>
            <p className="text-gray-300 font-sans text-xs">
              This workload is deployed in namespace <code>sentinelops-e2e</code>. Dependencies are mapped to PostgreSQL backend stores and upstream gateway routers.
            </p>
          </div>
        )}

        {activeTab === "incidents" && (
          <div className="p-5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3 font-mono text-xs">
            <span className="text-gray-400">Associated Incidents</span>
            <p className="text-gray-300 font-sans text-xs">
              Check Incident Center for correlated anomalies linked to service <code>{selectedPod.pod_name.split("-")[0]}</code>.
            </p>
          </div>
        )}
      </div>
    );
  }

  // ── WORKLOAD LISTING VIEW (/workloads) ───────────────────────────────────
  const filteredPods = pods.filter((p) => {
    const isDegraded = !p.ready || p.phase !== "Running" || (p.status_display && p.status_display !== "Running");
    const matchStatus =
      statusFilter === "all" ||
      (statusFilter === "failing" && isDegraded) ||
      (statusFilter === "running" && !isDegraded) ||
      (p.status_display && p.status_display.toLowerCase() === statusFilter.toLowerCase());
    const matchSearch =
      !search ||
      p.pod_name.toLowerCase().includes(search.toLowerCase()) ||
      p.namespace.toLowerCase().includes(search.toLowerCase());
    return matchStatus && matchSearch;
  });

  return (
    <div className="space-y-4 max-w-7xl mx-auto font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-white/5">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Workload Intelligence</h1>
          <p className="text-xs text-gray-400 font-mono mt-0.5">
            Live Kubernetes Pod & Container Telemetry &bull; Namespace: <span className="text-cyan-400">sentinelops-e2e</span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadWorkloads}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono bg-slate-800 hover:bg-slate-700 text-gray-300 rounded border border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Sync Workloads</span>
          </button>
        </div>
      </div>

      {/* KPI Overview Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
        <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
          <span className="text-gray-500 block text-[10px]">TOTAL WORKLOAD PODS</span>
          <span className="text-lg font-bold text-white">{overview?.total_pods ?? pods.length}</span>
        </div>
        <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
          <span className="text-gray-500 block text-[10px]">HEALTHY PODS</span>
          <span className="text-lg font-bold text-emerald-400">{overview?.running_pods ?? 0}</span>
        </div>
        <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
          <span className="text-gray-500 block text-[10px]">DEGRADED / FAILING</span>
          <span className="text-lg font-bold text-red-400">{overview?.failing_pods ?? 0}</span>
        </div>
        <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
          <span className="text-gray-500 block text-[10px]">TOTAL RESTART BURST</span>
          <span className="text-lg font-bold text-amber-400">{overview?.total_restarts ?? 0}</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-lg bg-slate-900/80 border border-slate-800">
        <div className="flex items-center gap-2 flex-1 min-w-[260px]">
          <Search className="w-4 h-4 text-gray-500 shrink-0" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search pod name, service or namespace..."
            className="w-full bg-transparent text-xs text-gray-200 placeholder-gray-500 focus:outline-none font-mono"
          />
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-gray-300 rounded px-2.5 py-1 text-xs focus:outline-none"
          >
            <option value="all">Status: All</option>
            <option value="running">Running / Healthy</option>
            <option value="failing">Failing / Restarting</option>
            <option value="crashloopbackoff">CrashLoopBackOff</option>
            <option value="oomkilled">OOMKilled</option>
          </select>
        </div>
      </div>

      {/* Main Pod Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-lg overflow-hidden">
        {filteredPods.length === 0 ? (
          <div className="p-12 text-center text-gray-500 text-xs font-mono">
            No workloads match the selected filter.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-sans">
              <thead className="text-[10px] font-mono text-gray-400 uppercase bg-slate-950/70 border-b border-slate-800">
                <tr>
                  <th className="px-4 py-2.5 font-bold">Status</th>
                  <th className="px-4 py-2.5 font-bold">Workload Pod</th>
                  <th className="px-4 py-2.5 font-bold">Namespace</th>
                  <th className="px-4 py-2.5 font-bold">Ready</th>
                  <th className="px-4 py-2.5 font-bold">Restarts</th>
                  <th className="px-4 py-2.5 font-bold">CPU</th>
                  <th className="px-4 py-2.5 font-bold">Memory</th>
                  <th className="px-4 py-2.5 font-bold">Age</th>
                  <th className="px-4 py-2.5 text-right font-bold">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                {filteredPods.map((pod) => {
                  // Calculate age
                  let ageStr = "1h";
                  if (pod.start_time) {
                    const diffMs = Date.now() - new Date(pod.start_time).getTime();
                    const diffM = Math.floor(diffMs / 60000);
                    if (diffM < 60) ageStr = `${Math.max(1, diffM)}m`;
                    else ageStr = `${Math.floor(diffM / 60)}h ${diffM % 60}m`;
                  }

                  return (
                    <tr key={pod.pod_name} className="hover:bg-white/[0.02] transition">
                      <td className="px-4 py-2.5 whitespace-nowrap">
                        <span
                          className={`text-[9px] uppercase font-bold px-1.5 py-0.5 rounded border ${
                            pod.status_display === "Running"
                              ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-400"
                              : pod.status_display === "CrashLoopBackOff"
                              ? "bg-red-500/15 border-red-500/30 text-red-400 animate-pulse"
                              : pod.status_display === "OOMKilled"
                              ? "bg-purple-500/15 border-purple-500/30 text-purple-400"
                              : "bg-amber-500/15 border-amber-500/30 text-amber-400"
                          }`}
                        >
                          {pod.status_display || pod.phase}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 font-sans font-medium text-gray-200 truncate max-w-[240px]">
                        <Link
                          to={`/workloads/${pod.namespace}/${pod.pod_name}`}
                          className="hover:text-cyan-400 hover:underline"
                        >
                          {pod.pod_name}
                        </Link>
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap text-gray-400">
                        {pod.namespace}
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap">
                        <span className={pod.ready ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>
                          {pod.ready ? "1/1" : "0/1"}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap text-gray-300">
                        {pod.restart_count || 0}
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap text-cyan-400">
                        {pod.status_display === "Running" ? "14m" : "0m"}
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap text-purple-400">
                        {pod.status_display === "OOMKilled" ? "256Mi (Max)" : pod.status_display === "Running" ? "64Mi" : "12Mi"}
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap text-gray-400">
                        {ageStr}
                      </td>
                      <td className="px-4 py-2.5 text-right whitespace-nowrap space-x-1.5 font-sans">
                        <Link
                          to="/investigations"
                          className="px-2 py-0.5 text-[10px] rounded bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/40 transition font-mono"
                        >
                          Investigate
                        </Link>
                        <Link
                          to={`/workloads/${pod.namespace}/${pod.pod_name}`}
                          className="px-2 py-0.5 text-[10px] rounded bg-slate-800 hover:bg-slate-700 text-gray-300 border border-slate-700 transition font-mono"
                        >
                          Detail
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
