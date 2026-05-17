import { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import AIInsightsPanel from "../components/dashboard/AIInsightsPanel";
import RCAPanel from "../components/dashboard/RCAPanel";
import RecommendationPanel from "../components/dashboard/RecommendationPanel";
import AdvancedTopologyVisualization from "../components/topology/AdvancedTopologyVisualization";
import { api, IncidentSummary, TopologyGraph } from "../lib/api";
import { useWebSocket } from "../hooks/useWebSocket";
import { motion, AnimatePresence } from "framer-motion";
import {
  Server, Zap, ShieldAlert, Cpu, Activity, Network,
  ArrowRight, ChevronRight, Clock, CheckCircle, AlertTriangle, TrendingUp
} from "lucide-react";

const SEVERITY_META: Record<string, { color: string; border: string; glow: string }> = {
  critical: { color: "text-red-400", border: "border-l-red-500", glow: "shadow-[0_0_12px_rgba(239,68,68,0.2)]" },
  high: { color: "text-orange-400", border: "border-l-orange-500", glow: "" },
  medium: { color: "text-yellow-400", border: "border-l-yellow-500", glow: "" },
  low: { color: "text-green-400", border: "border-l-green-500", glow: "" },
};

// Animated counter
function Counter({ value, className }: { value: number | string; className?: string }) {
  return (
    <motion.span
      key={String(value)}
      initial={{ y: 8, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={className}
    >
      {value}
    </motion.span>
  );
}

function HealthPill({ status }: { status: string }) {
  const ok = status === "healthy";
  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-[10px] font-mono uppercase tracking-widest border ${ok ? "border-green-500/30 bg-green-500/10 text-green-400" : "border-red-500/30 bg-red-500/10 text-red-400 animate-pulse"}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${ok ? "bg-green-400" : "bg-red-400"}`} />
      {status}
    </div>
  );
}

export default function Dashboard() {
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [topology, setTopology] = useState<TopologyGraph | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [rca, setRca] = useState<Record<string, unknown> | null>(null);
  const [recommendations, setRecommendations] = useState<Awaited<ReturnType<typeof api.recommendations>>>([]);
  const [insights, setInsights] = useState<Awaited<ReturnType<typeof api.insights>>>([]);
  const [health, setHealth] = useState("checking");
  const [chartData, setChartData] = useState<{ t: string; events: number; anomalies: number }[]>([]);
  const tickRef = useRef(0);

  const { connected, events, lastEvent } = useWebSocket((e) => {
    if (e.type === "topology" && e.payload?.nodes) setTopology(e.payload as unknown as TopologyGraph);
    if (e.type === "incident") refreshIncidents();
  });

  const refreshIncidents = () => {
    api.incidents().then(setIncidents).catch(() => setIncidents([]));
    api.topology().then(setTopology).catch(() => null);
  };

  useEffect(() => {
    api.health().then(h => setHealth(h.status)).catch(() => setHealth("down"));
    refreshIncidents();
  }, [lastEvent]);

  useEffect(() => {
    if (!selectedId) return;
    api.rca(selectedId).then(setRca).catch(() => setRca(null));
    api.recommendations(selectedId).then(setRecommendations).catch(() => setRecommendations([]));
    api.insights(selectedId).then(setInsights).catch(() => setInsights([]));
  }, [selectedId]);

  // Live-updating area chart
  useEffect(() => {
    const buildData = () => {
      const now = Date.now();
      return Array.from({ length: 20 }, (_, i) => ({
        t: i === 19 ? "now" : `-${(19 - i) * 15}s`,
        events: Math.max(0, events.length + Math.sin(i * 0.6 + tickRef.current * 0.1) * 8 + i * 1.2),
        anomalies: Math.max(0, incidents.length + Math.sin(i * 0.4 + tickRef.current * 0.08) * 3),
      }));
    };
    setChartData(buildData());
    const t = setInterval(() => {
      tickRef.current++;
      setChartData(buildData());
    }, 2000);
    return () => clearInterval(t);
  }, [events.length, incidents.length]);

  const criticalCount = incidents.filter(i => i.severity === "critical").length;

  const KPI_CARDS = [
    {
      label: "Core Status",
      value: health.toUpperCase(),
      sub: health === "healthy" ? "All services nominal" : "Degraded services detected",
      icon: <Cpu className="w-5 h-5" />,
      color: health === "healthy" ? "text-sentinel-success" : "text-sentinel-danger",
      borderColor: health === "healthy" ? "border-sentinel-success/25" : "border-sentinel-danger/40",
      accent: health === "healthy" ? "rgba(16,185,129,0.08)" : "rgba(239,68,68,0.08)",
    },
    {
      label: "Active Incidents",
      value: incidents.length,
      sub: `${criticalCount} critical · ${incidents.length - criticalCount} others`,
      icon: <ShieldAlert className="w-5 h-5" />,
      color: incidents.length > 0 ? "text-red-400" : "text-sentinel-accent",
      borderColor: incidents.length > 0 ? "border-red-500/30" : "border-sentinel-accent/25",
      accent: incidents.length > 0 ? "rgba(239,68,68,0.06)" : "rgba(34,211,238,0.04)",
    },
    {
      label: "Monitored Nodes",
      value: topology?.node_count ?? 0,
      sub: `${topology?.edge_count ?? 0} neural connections`,
      icon: <Server className="w-5 h-5" />,
      color: "text-blue-400",
      borderColor: "border-blue-500/25",
      accent: "rgba(59,130,246,0.05)",
    },
    {
      label: "Event Stream",
      value: events.length,
      sub: "Real-time telemetry ingestion",
      icon: <Zap className="w-5 h-5" />,
      color: "text-yellow-400",
      borderColor: "border-yellow-500/25",
      accent: "rgba(234,179,8,0.05)",
    },
  ];

  return (
    <div className="space-y-6 pb-4">
      {/* ── Header ── */}
      <header className="flex items-end justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-sentinel-accent/10 border border-sentinel-accent/30 rounded-xl flex items-center justify-center glow-border-accent">
            <Activity className="w-6 h-6 text-sentinel-accent animate-pulse-slow" />
          </div>
          <div>
            <h1 className="page-title glow-text-accent">Operations Center</h1>
            <p className="text-[10px] font-mono text-gray-500 uppercase tracking-widest mt-1">
              Global Infrastructure Intelligence · Autonomous Monitoring
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <HealthPill status={health} />
          <div className={`flex items-center gap-2 px-4 py-2 rounded-xl glass-panel border text-[10px] font-mono uppercase tracking-widest ${connected ? "border-sentinel-success/30 text-sentinel-success" : "border-sentinel-danger/30 text-sentinel-danger"}`}>
            <span className={`w-2 h-2 rounded-full ${connected ? "bg-sentinel-success animate-pulse" : "bg-sentinel-danger"}`} />
            {connected ? "Live Telemetry" : "Disconnected"}
          </div>
        </div>
      </header>

      {/* ── KPI Row ── */}
      <div className="grid grid-cols-4 gap-4">
        {KPI_CARDS.map((card, i) => (
          <motion.div
            key={card.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
            whileHover={{ y: -3, transition: { duration: 0.2 } }}
            className={`glass-panel rounded-xl p-5 border ${card.borderColor} relative overflow-hidden group cursor-default`}
            style={{ background: `linear-gradient(135deg, ${card.accent} 0%, transparent 60%)` }}
          >
            {/* Icon top-right */}
            <div className={`absolute top-4 right-4 opacity-20 group-hover:opacity-60 transition-opacity duration-300 ${card.color}`}>
              {card.icon}
            </div>
            <p className="text-[9px] font-mono text-gray-500 uppercase tracking-[0.2em] mb-2">{card.label}</p>
            <p className={`text-3xl font-display font-black tabular-nums leading-none ${card.color}`}>
              <Counter value={card.value} />
            </p>
            <p className="text-[10px] font-mono text-gray-600 mt-2">{card.sub}</p>
            {/* Bottom accent line */}
            <div className="absolute bottom-0 left-0 right-0 h-px" style={{ background: `linear-gradient(90deg, transparent, ${card.color.includes("accent") ? "#22d3ee" : card.color.includes("red") ? "#ef4444" : card.color.includes("blue") ? "#3b82f6" : "#eab308"}, transparent)` }} />
          </motion.div>
        ))}
      </div>

      {/* ── Main Grid ── */}
      <div className="grid grid-cols-12 gap-6">
        {/* Topology Preview — 8 cols */}
        <div className="col-span-8 space-y-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.99 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.15 }}
            className="glass-panel border border-sentinel-700/40 rounded-xl relative overflow-hidden"
            style={{ height: 380 }}
          >
            {/* Header bar */}
            <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-4 py-3 bg-gradient-to-b from-black/60 to-transparent">
              <div className="flex items-center gap-2">
                <Network className="w-3.5 h-3.5 text-sentinel-accent" />
                <span className="text-[10px] font-mono text-sentinel-accent uppercase tracking-widest">Neural Map Preview</span>
              </div>
              <Link to="/topology" className="flex items-center gap-1 text-[9px] font-mono text-gray-500 hover:text-sentinel-accent uppercase tracking-widest transition-colors group">
                Full View <ChevronRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>

            {topology && topology.nodes.length > 0 ? (
              <AdvancedTopologyVisualization
                graph={topology}
                showPressure={false}
                showHealth={true}
                showEdgeWeights={false}
                animateUpdates={true}
              />
            ) : (
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
                <div className="w-8 h-8 border-t-2 border-sentinel-accent rounded-full animate-spin" />
                <span className="text-[10px] font-mono text-gray-500 uppercase tracking-[0.2em]">Establishing Topology Uplink...</span>
              </div>
            )}
          </motion.div>

          {/* Event Velocity Chart */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
            className="glass-panel border border-sentinel-700/40 rounded-xl p-5"
          >
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-xs font-display font-semibold text-white">Event Velocity Stream</h3>
                <p className="text-[9px] font-mono text-gray-600 uppercase tracking-widest mt-0.5">Real-time telemetry · 20-point rolling window</p>
              </div>
              <div className="flex items-center gap-4 text-[9px] font-mono">
                <div className="flex items-center gap-1.5"><span className="w-2.5 h-px bg-sentinel-accent inline-block" />Events</div>
                <div className="flex items-center gap-1.5"><span className="w-2.5 h-px bg-red-400 inline-block" />Anomalies</div>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={120}>
              <AreaChart data={chartData} margin={{ top: 4, right: 0, bottom: 0, left: -30 }}>
                <defs>
                  <linearGradient id="gEvents" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#22d3ee" stopOpacity={0.02} />
                  </linearGradient>
                  <linearGradient id="gAnomalies" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="t" stroke="transparent" tick={{ fill: "#475569", fontSize: 8, fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} />
                <YAxis stroke="transparent" tick={{ fill: "#475569", fontSize: 8 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: "rgba(9,17,30,0.95)", border: "1px solid rgba(34,211,238,0.25)", borderRadius: 8, fontSize: 10, fontFamily: "JetBrains Mono" }}
                  itemStyle={{ color: "#22d3ee" }}
                  cursor={{ stroke: "rgba(34,211,238,0.2)", strokeWidth: 1 }}
                />
                <Area type="monotoneX" dataKey="events" stroke="#22d3ee" strokeWidth={1.5} fillOpacity={1} fill="url(#gEvents)" dot={false} activeDot={{ r: 3, fill: "#22d3ee", strokeWidth: 0 }} />
                <Area type="monotoneX" dataKey="anomalies" stroke="#ef4444" strokeWidth={1} fillOpacity={1} fill="url(#gAnomalies)" dot={false} activeDot={{ r: 3, fill: "#ef4444", strokeWidth: 0 }} />
              </AreaChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        {/* Right col — Incidents + RCA */}
        <div className="col-span-4 space-y-4">
          {/* Active Incidents */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-panel border border-sentinel-700/40 rounded-xl overflow-hidden"
          >
            <div className="px-4 py-3 border-b border-sentinel-700/40 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-400" />
                <h3 className="text-xs font-display font-semibold text-white">Active Anomalies</h3>
              </div>
              <div className="flex items-center gap-2">
                {criticalCount > 0 && (
                  <span className="animate-pulse text-[9px] px-2 py-0.5 rounded-full bg-red-500/20 border border-red-500/30 text-red-400 font-mono">{criticalCount} CRITICAL</span>
                )}
                <Link to="/incidents" className="text-[9px] font-mono text-gray-600 hover:text-sentinel-accent uppercase tracking-widest transition-colors">
                  All →
                </Link>
              </div>
            </div>

            <div className="overflow-y-auto max-h-72 divide-y divide-sentinel-700/20">
              <AnimatePresence>
                {incidents.slice(0, 8).map((inc) => {
                  const meta = SEVERITY_META[inc.severity] ?? SEVERITY_META.low;
                  return (
                    <motion.button
                      key={inc.id}
                      initial={{ opacity: 0, x: 10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, height: 0 }}
                      onClick={() => setSelectedId(inc.id)}
                      className={`w-full text-left px-4 py-3 hover:bg-white/3 transition-all border-l-2 ${meta.border} ${selectedId === inc.id ? "bg-white/4" : ""} ${meta.glow}`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className={`text-[9px] font-mono uppercase tracking-widest px-1.5 py-0.5 rounded border ${inc.severity === "critical" ? "border-red-500/30 bg-red-500/10 text-red-400" :
                            inc.severity === "high" ? "border-orange-500/30 bg-orange-500/10 text-orange-400" : "border-yellow-500/30 bg-yellow-500/10 text-yellow-400"
                          }`}>{inc.severity}</span>
                        <span className="text-[9px] font-mono text-gray-600">{new Date(inc.started_at).toLocaleTimeString()}</span>
                      </div>
                      <Link to={`/incidents/${inc.id}`} className="text-xs font-sans text-gray-300 hover:text-white line-clamp-2 block mt-1 text-left leading-snug">
                        {inc.title}
                      </Link>
                      {inc.root_service && (
                        <p className="text-[9px] font-mono text-sentinel-accent/60 mt-1">svc/{inc.root_service}</p>
                      )}
                    </motion.button>
                  );
                })}
              </AnimatePresence>
              {incidents.length === 0 && (
                <div className="flex flex-col items-center justify-center py-12 gap-3">
                  <CheckCircle className="w-8 h-8 text-sentinel-success/40" />
                  <p className="text-[10px] font-mono text-gray-600 uppercase tracking-widest">All systems nominal</p>
                </div>
              )}
            </div>
          </motion.div>

          {/* RCA panel */}
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
            <RCAPanel rca={rca} />
          </motion.div>
        </div>
      </div>

      {/* ── Bottom Grid — AI Insights + Recommendations ── */}
      <div className="grid grid-cols-2 gap-6">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}>
          <AIInsightsPanel insights={insights as any} wsEvents={events} />
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.42 }}>
          <RecommendationPanel items={recommendations} />
        </motion.div>
      </div>
    </div>
  );
}
