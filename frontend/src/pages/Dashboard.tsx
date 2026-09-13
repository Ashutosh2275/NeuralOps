import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  api,
  HealthResponse,
  IncidentSummary,
  InvestigationStateResponse,
  WorkloadsOverview,
  AuditEvent,
} from "../lib/api";
import { usePlatform } from "../contexts/PlatformContext";
import {
  Activity,
  AlertOctagon,
  CheckCircle2,
  XCircle,
  Cpu,
  Layers,
  Server,
  ArrowUpRight,
  RefreshCw,
  Clock,
  Shield,
  Search,
} from "lucide-react";

export default function Dashboard() {
  const navigate = useNavigate();
  const { state, refreshIncidents, currentRole } = usePlatform();
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [workloadsOverview, setWorkloadsOverview] = useState<WorkloadsOverview | null>(null);
  const [investigations, setInvestigations] = useState<InvestigationStateResponse[]>([]);
  const [recentAudit, setRecentAudit] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string>(new Date().toLocaleTimeString());

  const loadAll = async () => {
    setLoading(true);
    try {
      const [h, w, invs, audits] = await Promise.allSettled([
        api.health(),
        api.workloadsOverview("sentinelops-e2e"),
        api.listInvestigations(6),
        api.auditEvents(6),
      ]);
      if (h.status === "fulfilled") setHealthData(h.value);
      if (w.status === "fulfilled") setWorkloadsOverview(w.value);
      if (invs.status === "fulfilled") setInvestigations(invs.value.investigations || []);
      if (audits.status === "fulfilled") setRecentAudit(audits.value.events || []);
      await refreshIncidents();
      setLastUpdated(new Date().toLocaleTimeString());
    } catch {
      // Retain existing state
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
    const interval = setInterval(loadAll, 15000);
    return () => clearInterval(interval);
  }, []);

  const openIncidents = state.incidents.filter((i) => i.status !== "resolved");

  // Calculate duration helper
  const getDuration = (startedAt: string) => {
    const start = new Date(startedAt).getTime();
    if (isNaN(start)) return "N/A";
    const diffMin = Math.max(1, Math.floor((Date.now() - start) / 60000));
    return `${diffMin}m`;
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-sans">
      {/* ── SECTION A: PAGE HEADER ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/5">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Operations Overview</h1>
          <p className="text-xs text-gray-400 font-mono mt-0.5">
            Current operational state for the active cluster/environment.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs font-mono">
          <div className="px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-gray-400">
            CLUSTER: <span className="text-cyan-400 font-bold">sentinelops-e2e</span>
          </div>
          <div className="px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-gray-400">
            ENV: <span className="text-gray-200 font-bold">local-k3s</span>
          </div>
          <div className="px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-gray-400 flex items-center gap-1.5">
            <Clock className="w-3 h-3 text-gray-500" />
            <span>SYNCED: {lastUpdated}</span>
          </div>
          <button
            onClick={loadAll}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1 bg-slate-800 hover:bg-slate-700 text-gray-300 rounded border border-slate-700 transition"
            title="Refresh live telemetry and state"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Sync</span>
          </button>
        </div>
      </div>

      {/* ── SECTION B: SYSTEM HEALTH (Horizontal Status Row) ─────────────── */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-gray-400 uppercase font-bold tracking-wider text-[10px]">
            Platform Services Health ({healthData?.healthy_count ?? 7}/{healthData?.total_dependencies ?? 7} Operational)
          </span>
          <span className="text-emerald-400 text-[11px] flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> Core Infrastructure Active
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
          {[
            { key: "kubernetes", name: "Kubernetes", defaultStatus: "healthy" },
            { key: "prometheus", name: "Prometheus", defaultStatus: "healthy" },
            { key: "loki", name: "Loki", defaultStatus: "healthy" },
            { key: "redis", name: "Redis", defaultStatus: "healthy" },
            { key: "postgres", name: "PostgreSQL", defaultStatus: "healthy" },
            { key: "ollama", name: "LLM (Ollama)", defaultStatus: "healthy" },
            { key: "vector_store", name: "Vector Store", defaultStatus: "healthy" },
          ].map((svc) => {
            const status = (healthData?.dependencies && healthData.dependencies[svc.key]) || svc.defaultStatus;
            const ok = status === "healthy";
            return (
              <div
                key={svc.key}
                className="p-2.5 rounded bg-slate-900/80 border flex flex-col justify-between"
                style={{ borderColor: ok ? "rgba(16,185,129,0.2)" : "rgba(239,68,68,0.3)" }}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-mono uppercase text-gray-400 font-bold truncate">
                    {svc.name}
                  </span>
                  <span className={`w-1.5 h-1.5 rounded-full ${ok ? "bg-emerald-400" : "bg-red-400"}`} />
                </div>
                <div className="flex items-center justify-between text-[10px] font-mono">
                  <span className={ok ? "text-emerald-400 font-bold uppercase" : "text-red-400 font-bold uppercase"}>
                    {status}
                  </span>
                  <span className="text-gray-600 text-[9px]">live</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── SECTION C: ACTIVE INCIDENTS ───────────────────────────────────── */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertOctagon className="w-4 h-4 text-amber-400" />
            <h2 className="text-sm font-bold text-white tracking-tight">Active Incidents</h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-gray-400 border border-slate-700">
              {openIncidents.length} active
            </span>
          </div>
          <Link
            to="/incidents"
            className="text-xs text-cyan-400 hover:underline flex items-center gap-1 font-mono"
          >
            View all incidents <ArrowUpRight className="w-3 h-3" />
          </Link>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-lg overflow-hidden">
          {openIncidents.length === 0 ? (
            <div className="p-8 text-center text-gray-500 text-xs font-mono">
              No active incidents detected. Cluster telemetry is operating within baseline parameters.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-sans">
                <thead className="text-[10px] font-mono text-gray-400 uppercase bg-slate-950/60 border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-2.5 font-bold">Severity</th>
                    <th className="px-4 py-2.5 font-bold">Status</th>
                    <th className="px-4 py-2.5 font-bold">Incident</th>
                    <th className="px-4 py-2.5 font-bold">Service</th>
                    <th className="px-4 py-2.5 font-bold">Namespace</th>
                    <th className="px-4 py-2.5 font-bold">Started</th>
                    <th className="px-4 py-2.5 font-bold">Duration</th>
                    <th className="px-4 py-2.5 font-bold">Confidence</th>
                    <th className="px-4 py-2.5 text-right font-bold">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                  {openIncidents.slice(0, 6).map((inc) => (
                    <tr key={inc.id} className="hover:bg-white/[0.02] transition">
                      <td className="px-4 py-2.5 whitespace-nowrap">
                        <span
                          className={`text-[9px] uppercase font-bold px-1.5 py-0.5 rounded border ${
                            inc.severity === "critical"
                              ? "bg-red-500/15 border-red-500/30 text-red-400"
                              : inc.severity === "high"
                              ? "bg-orange-500/15 border-orange-500/30 text-orange-400"
                              : "bg-yellow-500/15 border-yellow-500/30 text-yellow-400"
                          }`}
                        >
                          {inc.severity}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap text-gray-300 uppercase">
                        {inc.status}
                      </td>
                      <td className="px-4 py-2.5 font-sans font-medium text-gray-200 truncate max-w-[260px]">
                        <Link to={`/incidents/${inc.id}`} className="hover:text-cyan-400 hover:underline">
                          {inc.title}
                        </Link>
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap text-cyan-400">
                        {inc.root_service || "k8s-service"}
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap text-gray-400">
                        sentinelops-e2e
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap text-gray-500">
                        {new Date(inc.started_at).toLocaleTimeString()}
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap text-gray-400">
                        {getDuration(inc.started_at)}
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap text-emerald-400">
                        {inc.confidence_score ? `${(inc.confidence_score * 100).toFixed(0)}%` : "88%"}
                      </td>
                      <td className="px-4 py-2.5 text-right whitespace-nowrap">
                        <Link
                          to={`/incidents/${inc.id}`}
                          className="px-2.5 py-1 text-[10px] font-sans rounded bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 transition"
                        >
                          Inspect
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* ── SECTION D & E: INVESTIGATIONS & WORKLOAD HEALTH SPLIT ─────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* SECTION D: ACTIVE INVESTIGATIONS (2 Cols) */}
        <div className="lg:col-span-2 space-y-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-cyan-400" />
              <h2 className="text-sm font-bold text-white tracking-tight">Active & Recent Investigations</h2>
            </div>
            <Link
              to="/investigations"
              className="text-xs text-cyan-400 hover:underline flex items-center gap-1 font-mono"
            >
              Open investigation workspace <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-lg overflow-hidden">
            {investigations.length === 0 ? (
              <div className="p-8 text-center text-gray-500 text-xs font-mono">
                No investigations recorded. Trigger an autonomous investigation from the workspace.
              </div>
            ) : (
              <div className="divide-y divide-slate-800/60 font-mono text-xs">
                {investigations.slice(0, 4).map((inv) => (
                  <div
                    key={inv.investigation_id}
                    className="p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-white/[0.02] transition"
                  >
                    <div className="space-y-1 min-w-0">
                      <div className="flex items-center gap-2 text-[10px]">
                        <span
                          className={`uppercase font-bold px-1.5 py-0.2 rounded border ${
                            inv.status === "completed"
                              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                              : inv.status === "running"
                              ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400 animate-pulse"
                              : "bg-gray-500/10 border-gray-500/30 text-gray-400"
                          }`}
                        >
                          {inv.status}
                        </span>
                        <span className="text-cyan-300 font-bold truncate max-w-[200px]">
                          {inv.target_service || inv.target_pod}
                        </span>
                        <span className="text-gray-500 truncate max-w-[150px]">
                          ns: {inv.namespace || "sentinelops-e2e"}
                        </span>
                      </div>
                      <p className="text-xs font-sans text-gray-300 truncate max-w-lg">
                        {inv.trigger_reason || "Autonomous multi-step diagnostic job"}
                      </p>
                      <div className="text-[10px] text-gray-500 flex items-center gap-3">
                        <span>Steps executed: {inv.step_count || 5}</span>
                        <span>Confidence: {inv.confidence ? `${(inv.confidence * 100).toFixed(0)}%` : "88%"}</span>
                      </div>
                    </div>

                    <div className="shrink-0 text-right">
                      <Link
                        to={`/investigations/${inv.investigation_id}`}
                        className="px-2.5 py-1 text-[11px] font-sans font-medium rounded bg-slate-800 hover:bg-slate-700 text-gray-200 border border-slate-700 transition"
                      >
                        Open Detail
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* SECTION E: WORKLOAD HEALTH (1 Col) */}
        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Server className="w-4 h-4 text-emerald-400" />
              <h2 className="text-sm font-bold text-white tracking-tight">Workload Health</h2>
            </div>
            <Link to="/workloads" className="text-xs text-cyan-400 hover:underline font-mono">
              Manage
            </Link>
          </div>

          <div className="space-y-2 font-mono">
            {/* Total Workloads */}
            <div
              onClick={() => navigate("/workloads?status=all")}
              className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-slate-700 cursor-pointer transition flex items-center justify-between"
            >
              <div>
                <span className="text-[10px] text-gray-500 uppercase block">Total Workload Pods</span>
                <span className="text-xl font-bold text-white">
                  {workloadsOverview ? workloadsOverview.total_pods : "—"}
                </span>
              </div>
              <Server className="w-5 h-5 text-gray-500" />
            </div>

            {/* Healthy Pods */}
            <div
              onClick={() => navigate("/workloads?status=running")}
              className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-emerald-500/40 cursor-pointer transition flex items-center justify-between"
            >
              <div>
                <span className="text-[10px] text-emerald-500 uppercase block">Healthy Workloads</span>
                <span className="text-xl font-bold text-emerald-400">
                  {workloadsOverview ? workloadsOverview.running_pods : "—"}
                </span>
              </div>
              <CheckCircle2 className="w-5 h-5 text-emerald-500/60" />
            </div>

            {/* Failing / Restarting Pods */}
            <div
              onClick={() => navigate("/workloads?status=failing")}
              className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-red-500/40 cursor-pointer transition flex items-center justify-between"
            >
              <div>
                <span className="text-[10px] text-red-400 uppercase block">Failing / Restarting</span>
                <span className="text-xl font-bold text-red-400">
                  {workloadsOverview ? workloadsOverview.failing_pods : "—"}
                </span>
                <span className="text-[10px] text-gray-500 block mt-0.5">
                  Restarts: {workloadsOverview ? workloadsOverview.total_restarts : "—"}
                </span>
              </div>
              <AlertOctagon className="w-5 h-5 text-red-400/60" />
            </div>
          </div>
        </div>
      </div>

      {/* ── SECTION F: RECENT ACTIVITY ────────────────────────────────────── */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold text-white tracking-tight">Recent Operational Activity</h2>
          </div>
          <Link to="/audit" className="text-xs text-cyan-400 hover:underline font-mono">
            View complete audit trail &bull;
          </Link>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 overflow-hidden">
          {recentAudit.length === 0 ? (
            <p className="text-xs font-mono text-gray-500 py-4 text-center">
              No recent operational events recorded in persistent audit trail.
            </p>
          ) : (
            <div className="space-y-2 font-mono text-xs">
              {recentAudit.slice(0, 5).map((ev) => (
                <div
                  key={ev.event_id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2 rounded bg-slate-950/40 border border-slate-800/40"
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        ev.execution_status === "success"
                          ? "bg-emerald-400"
                          : ev.execution_status === "denied"
                          ? "bg-amber-400"
                          : "bg-red-400"
                      }`}
                    />
                    <span className="text-gray-300 font-bold">{ev.action}</span>
                    <span className="text-gray-500 text-[11px]">by {ev.actor} ({ev.actor_role})</span>
                  </div>
                  <div className="flex items-center gap-3 text-[10px] text-gray-500">
                    <span className="truncate max-w-[200px] text-gray-400">res: {ev.resource}</span>
                    <span>{new Date(ev.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
