import { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import { api, IncidentSummary } from "../lib/api";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldAlert, AlertTriangle, Clock, ChevronRight, Search, Filter } from "lucide-react";

const SEV_CONFIG = {
  critical: { border: "border-l-red-500", bg: "bg-red-500/8", badge: "bg-red-500/20 text-red-400 border-red-500/40", glow: "shadow-[0_0_15px_rgba(239,68,68,0.15)]" },
  high:     { border: "border-l-orange-500", bg: "bg-orange-500/8", badge: "bg-orange-500/20 text-orange-400 border-orange-500/40", glow: "" },
  medium:   { border: "border-l-yellow-500", bg: "bg-yellow-500/8", badge: "bg-yellow-500/20 text-yellow-400 border-yellow-500/40", glow: "" },
  low:      { border: "border-l-green-500", bg: "bg-green-500/8", badge: "bg-green-500/20 text-green-400 border-green-500/40", glow: "" },
};

export default function Incidents() {
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [animating, setAnimating] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    api.incidents().then(setIncidents).finally(() => setLoading(false));
    // Refresh every 5s for live feel
    intervalRef.current = setInterval(() => {
      api.incidents().then(setIncidents);
    }, 5000);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, []);

  const filtered = incidents.filter((i) => {
    const matchSev = filter === "all" || i.severity === filter;
    const matchSearch = !search || i.title.toLowerCase().includes(search.toLowerCase()) || (i.root_service ?? "").toLowerCase().includes(search.toLowerCase());
    return matchSev && matchSearch;
  });

  const counts = {
    critical: incidents.filter(i => i.severity === "critical").length,
    high: incidents.filter(i => i.severity === "high").length,
    medium: incidents.filter(i => i.severity === "medium").length,
    low: incidents.filter(i => i.severity === "low").length,
  };

  return (
    <div className="flex flex-col gap-6 min-h-0 p-6 rounded-2xl border border-white/5 shadow-[0_0_50px_rgba(0,0,0,0.5)]" style={{ height: "calc(100vh - 128px)", background: "rgba(6, 13, 24, 0.6)", backdropFilter: "blur(12px)" }}>
      {/* Header */}
      <header className="flex justify-between items-end">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center justify-center shadow-[0_0_20px_rgba(239,68,68,0.2)]">
            <ShieldAlert size={24} className="text-red-400 animate-pulse-slow" />
          </div>
          <div>
            <h1 className="text-3xl font-display font-bold text-white tracking-tight uppercase" style={{ textShadow: "0 0 15px rgba(239,68,68,0.4)" }}>
              Incident Registry
            </h1>
            <p className="text-sm text-red-400/70 font-sans tracking-widest uppercase mt-1">
              {incidents.length} anomalies detected
            </p>
          </div>
        </div>

        {/* Severity summary pills */}
        <div className="flex gap-3">
          {(Object.entries(counts) as [string, number][]).map(([sev, cnt]) => (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.96 }}
              key={sev}
              onClick={() => setFilter(filter === sev ? "all" : sev)}
              className={`px-4 py-2 rounded-lg border text-xs font-mono uppercase tracking-widest transition-all ${
                (SEV_CONFIG as any)[sev].badge
              } ${filter === sev ? "ring-1 ring-white/20" : "opacity-70 hover:opacity-100"}`}
            >
              {cnt} {sev}
            </motion.button>
          ))}
        </div>
      </header>

      {/* Search bar */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search incidents, services..."
          className="w-full glass-panel rounded-xl pl-10 pr-4 py-3 text-sm font-mono text-gray-300 focus:outline-none focus:border-sentinel-accent/50 border border-sentinel-700/50 placeholder-gray-600"
        />
      </div>

      {/* Incidents List */}
      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <div className="w-10 h-10 rounded-full border-t-2 border-red-500 animate-spin" />
            <span className="text-red-400 font-mono text-xs uppercase tracking-widest animate-pulse">Loading Incident Registry...</span>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col gap-3 overflow-y-auto pr-2 min-h-0 scrollbar-thin scrollbar-thumb-cyan-500/20 scrollbar-track-transparent">
          <AnimatePresence mode="popLayout">
            {filtered.map((inc, i) => {
              const cfg = (SEV_CONFIG as any)[inc.severity] ?? SEV_CONFIG.low;
              return (
                <motion.div key={inc.id} layout initial={{ opacity: 0, x: -20, filter: "blur(4px)" }} animate={{ opacity: 1, x: 0, filter: "blur(0px)" }} exit={{ opacity: 0, scale: 0.95 }} transition={{ type: "spring", stiffness: 350, damping: 25 }} >
                  <Link to={`/incidents/${inc.id}`}>
                    <div className={`glass-panel border-l-4 ${cfg.border} ${cfg.bg} ${cfg.glow} rounded-xl p-5 group hover:bg-white/5 transition-all duration-300 flex items-start gap-5`}>
                      {/* Severity indicator */}
                      <div className="flex flex-col items-center gap-1 pt-1">
                        <AlertTriangle size={18} className={inc.severity === "critical" ? "text-red-400 animate-pulse" : "text-gray-500"} />
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-4 mb-2">
                          <h3 className="text-base font-bold text-white font-sans truncate group-hover:text-sentinel-accent transition-colors">
                            {inc.title}
                          </h3>
                          <span className={`shrink-0 text-[10px] px-2.5 py-1 rounded border font-mono uppercase tracking-widest ${cfg.badge}`}>
                            {inc.severity}
                          </span>
                        </div>

                        <div className="flex flex-wrap gap-4 text-xs font-mono">
                          <span className="text-gray-400">
                            <span className="text-gray-600 mr-1">SVC</span>
                            <span className="text-sentinel-accent">{inc.root_service ?? "â€”"}</span>
                          </span>
                          <span className="text-gray-400">
                            <span className="text-gray-600 mr-1">CONF</span>
                            <span className="text-green-400">{inc.confidence_score != null ? `${(inc.confidence_score * 100).toFixed(0)}%` : "â€”"}</span>
                          </span>
                          <span className="text-gray-400 flex items-center gap-1">
                            <Clock size={11} className="text-gray-600" />
                            {new Date(inc.started_at).toLocaleString()}
                          </span>
                          <span className={`px-2 py-0.5 rounded text-[10px] uppercase tracking-wider ${inc.status === "investigating" ? "bg-blue-500/20 text-blue-400" : "bg-gray-700/50 text-gray-400"}`}>
                            {inc.status}
                          </span>
                        </div>
                      </div>

                      {/* Arrow */}
                      <ChevronRight size={18} className="text-gray-600 group-hover:text-sentinel-accent transition-colors group-hover:translate-x-1 transition-transform shrink-0 mt-1" />
                    </div>
                  </Link>
                </motion.div>
              );
            })}
          </AnimatePresence>

          {filtered.length === 0 && !loading && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex-1 flex flex-col items-center justify-center py-20 text-center">
              <div className="w-16 h-16 rounded-full border border-dashed border-gray-700 flex items-center justify-center mb-4">
                <ShieldAlert size={28} className="text-gray-700" />
              </div>
              <p className="text-gray-500 font-mono text-sm uppercase tracking-widest">No anomalies detected</p>
              <p className="text-gray-700 text-xs mt-2 font-mono">System operating within normal parameters</p>
            </motion.div>
          )}
        </div>
      )}
    </div>
  );
}





