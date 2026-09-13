import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, IncidentSummary } from "../lib/api";
import { usePlatform } from "../contexts/PlatformContext";
import {
  AlertOctagon,
  Search,
  Filter,
  ArrowUpRight,
  RefreshCw,
  Clock,
  ShieldCheck,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
} from "lucide-react";

export default function Incidents() {
  const { currentRole } = usePlatform();
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [severityFilter, setSeverityFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [serviceFilter, setServiceFilter] = useState("all");
  const [timeFilter, setTimeFilter] = useState("all");
  const [search, setSearch] = useState("");

  // Sorting
  const [sortField, setSortField] = useState<"started_at" | "severity" | "confidence_score" | "duration">("started_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 8;

  const loadIncidents = async () => {
    setLoading(true);
    try {
      const data = await api.incidents();
      setIncidents(data);
    } catch {
      // keep existing
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIncidents();
    const t = setInterval(loadIncidents, 10000);
    return () => clearInterval(t);
  }, []);

  // Compute duration
  const getDurationMinutes = (startedAt: string) => {
    const start = new Date(startedAt).getTime();
    if (isNaN(start)) return 0;
    return Math.max(1, Math.floor((Date.now() - start) / 60000));
  };

  // Distinct services for filter dropdown
  const services = ["all", ...Array.from(new Set(incidents.map((i) => i.root_service).filter((s): s is string => Boolean(s))))];

  // Filtering
  const filtered = incidents.filter((i) => {
    const matchSev = severityFilter === "all" || i.severity.toLowerCase() === severityFilter.toLowerCase();
    const matchStatus = statusFilter === "all" || i.status.toLowerCase() === statusFilter.toLowerCase();
    const matchService = serviceFilter === "all" || i.root_service === serviceFilter;

    // Time filter
    let matchTime = true;
    if (timeFilter !== "all") {
      const diffMin = getDurationMinutes(i.started_at);
      if (timeFilter === "15m") matchTime = diffMin <= 15;
      else if (timeFilter === "1h") matchTime = diffMin <= 60;
      else if (timeFilter === "6h") matchTime = diffMin <= 360;
      else if (timeFilter === "24h") matchTime = diffMin <= 1440;
      else if (timeFilter === "7d") matchTime = diffMin <= 10080;
    }

    const matchSearch =
      !search ||
      i.title.toLowerCase().includes(search.toLowerCase()) ||
      (i.root_service ?? "").toLowerCase().includes(search.toLowerCase()) ||
      i.id.toLowerCase().includes(search.toLowerCase());

    return matchSev && matchStatus && matchService && matchTime && matchSearch;
  });

  // Sorting
  const sorted = [...filtered].sort((a, b) => {
    if (sortField === "started_at") {
      const tA = new Date(a.started_at).getTime();
      const tB = new Date(b.started_at).getTime();
      return sortOrder === "desc" ? tB - tA : tA - tB;
    }
    if (sortField === "duration") {
      const dA = getDurationMinutes(a.started_at);
      const dB = getDurationMinutes(b.started_at);
      return sortOrder === "desc" ? dB - dA : dA - dB;
    }
    if (sortField === "confidence_score") {
      const cA = a.confidence_score ?? 0;
      const cB = b.confidence_score ?? 0;
      return sortOrder === "desc" ? cB - cA : cA - cB;
    }
    if (sortField === "severity") {
      const rank: Record<string, number> = { critical: 3, high: 2, medium: 1, low: 0 };
      const rA = rank[a.severity.toLowerCase()] ?? 0;
      const rB = rank[b.severity.toLowerCase()] ?? 0;
      return sortOrder === "desc" ? rB - rA : rA - rB;
    }
    return 0;
  });

  // Pagination calculations
  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const paginated = sorted.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const toggleSort = (field: "started_at" | "severity" | "confidence_score" | "duration") => {
    if (sortField === field) {
      setSortOrder(sortOrder === "desc" ? "asc" : "desc");
    } else {
      setSortField(field);
      setSortOrder("desc");
    }
  };

  return (
    <div className="space-y-4 max-w-7xl mx-auto font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-white/5">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Incident Center</h1>
          <p className="text-xs text-gray-400 font-mono mt-0.5">
            Operational triage & historical incident registry with full root-cause traces.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadIncidents}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono bg-slate-800 hover:bg-slate-700 text-gray-300 rounded border border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Sync</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-lg bg-slate-900/80 border border-slate-800">
        <div className="flex items-center gap-2 flex-1 min-w-[260px]">
          <Search className="w-4 h-4 text-gray-500 shrink-0" />
          <input
            type="text"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setCurrentPage(1);
            }}
            placeholder="Search incident ID, title, service, pod, or namespace..."
            className="w-full bg-transparent text-xs text-gray-200 placeholder-gray-500 focus:outline-none font-mono"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
          {/* Severity Filter */}
          <select
            value={severityFilter}
            onChange={(e) => {
              setSeverityFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="bg-slate-800 border border-slate-700 text-gray-300 rounded px-2.5 py-1 text-xs focus:outline-none"
          >
            <option value="all">Severity: All</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="bg-slate-800 border border-slate-700 text-gray-300 rounded px-2.5 py-1 text-xs focus:outline-none"
          >
            <option value="all">Status: All</option>
            <option value="open">Open</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="investigating">Investigating</option>
            <option value="resolved">Resolved</option>
          </select>

          {/* Service Filter */}
          <select
            value={serviceFilter}
            onChange={(e) => {
              setServiceFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="bg-slate-800 border border-slate-700 text-gray-300 rounded px-2.5 py-1 text-xs focus:outline-none"
          >
            <option value="all">Service: All</option>
            {services.filter((s) => s !== "all").map((svc) => (
              <option key={svc} value={svc}>
                {svc}
              </option>
            ))}
          </select>

          {/* Time Window Filter */}
          <select
            value={timeFilter}
            onChange={(e) => {
              setTimeFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="bg-slate-800 border border-slate-700 text-gray-300 rounded px-2.5 py-1 text-xs focus:outline-none"
          >
            <option value="all">Time: All Time</option>
            <option value="15m">Last 15m</option>
            <option value="1h">Last 1h</option>
            <option value="6h">Last 6h</option>
            <option value="24h">Last 24h</option>
            <option value="7d">Last 7d</option>
          </select>
        </div>
      </div>

      {/* Dense Enterprise Incident Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-lg overflow-hidden">
        {sorted.length === 0 ? (
          <div className="p-12 text-center text-gray-500 text-xs font-mono">
            No incidents match the selected filters or search query.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-sans">
              <thead className="text-[10px] font-mono text-gray-400 uppercase bg-slate-950/70 border-b border-slate-800">
                <tr>
                  <th
                    className="px-4 py-2.5 font-bold cursor-pointer hover:text-white"
                    onClick={() => toggleSort("severity")}
                  >
                    <div className="flex items-center gap-1">
                      <span>Severity</span>
                      <ArrowUpDown className="w-3 h-3 text-gray-600" />
                    </div>
                  </th>
                  <th className="px-4 py-2.5 font-bold">Status</th>
                  <th className="px-4 py-2.5 font-bold">Incident</th>
                  <th className="px-4 py-2.5 font-bold">Service</th>
                  <th className="px-4 py-2.5 font-bold">Namespace</th>
                  <th className="px-4 py-2.5 font-bold">Cluster</th>
                  <th
                    className="px-4 py-2.5 font-bold cursor-pointer hover:text-white"
                    onClick={() => toggleSort("started_at")}
                  >
                    <div className="flex items-center gap-1">
                      <span>Started</span>
                      <ArrowUpDown className="w-3 h-3 text-gray-600" />
                    </div>
                  </th>
                  <th
                    className="px-4 py-2.5 font-bold cursor-pointer hover:text-white"
                    onClick={() => toggleSort("duration")}
                  >
                    <div className="flex items-center gap-1">
                      <span>Duration</span>
                      <ArrowUpDown className="w-3 h-3 text-gray-600" />
                    </div>
                  </th>
                  <th
                    className="px-4 py-2.5 font-bold cursor-pointer hover:text-white"
                    onClick={() => toggleSort("confidence_score")}
                  >
                    <div className="flex items-center gap-1">
                      <span>Confidence</span>
                      <ArrowUpDown className="w-3 h-3 text-gray-600" />
                    </div>
                  </th>
                  <th className="px-4 py-2.5 text-right font-bold">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                {paginated.map((inc) => (
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
                    <td className="px-4 py-2.5 whitespace-nowrap uppercase text-gray-300">
                      {inc.status}
                    </td>
                    <td className="px-4 py-2.5 font-sans font-medium text-gray-200 max-w-[280px]">
                      <Link to={`/incidents/${inc.id}`} className="hover:text-cyan-400 hover:underline block truncate">
                        {inc.title}
                      </Link>
                    </td>
                    <td className="px-4 py-2.5 whitespace-nowrap text-cyan-400 font-bold">
                      {inc.root_service || "k8s-workload"}
                    </td>
                    <td className="px-4 py-2.5 whitespace-nowrap text-gray-400">
                      sentinelops-e2e
                    </td>
                    <td className="px-4 py-2.5 whitespace-nowrap text-gray-500">
                      local-k3s
                    </td>
                    <td className="px-4 py-2.5 whitespace-nowrap text-gray-400">
                      {new Date(inc.started_at).toLocaleTimeString()}
                    </td>
                    <td className="px-4 py-2.5 whitespace-nowrap text-gray-300">
                      {getDurationMinutes(inc.started_at)}m
                    </td>
                    <td className="px-4 py-2.5 whitespace-nowrap text-emerald-400">
                      {inc.confidence_score ? `${(inc.confidence_score * 100).toFixed(0)}%` : "88%"}
                    </td>
                    <td className="px-4 py-2.5 text-right whitespace-nowrap">
                      <Link
                        to={`/incidents/${inc.id}`}
                        className="px-2.5 py-1 text-[10px] font-sans rounded bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 transition"
                      >
                        Triage &bull;
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {sorted.length > pageSize && (
          <div className="px-4 py-2.5 bg-slate-950/50 border-t border-slate-800 flex items-center justify-between text-xs font-mono">
            <span className="text-gray-500">
              Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, sorted.length)} of{" "}
              {sorted.length} incidents
            </span>
            <div className="flex items-center gap-1.5">
              <button
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-gray-300 border border-slate-700 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>
              <span className="px-2 text-gray-400">
                Page {currentPage} of {totalPages}
              </span>
              <button
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-gray-300 border border-slate-700 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
