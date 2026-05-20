import { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import AIInsightsPanel from "../components/dashboard/AIInsightsPanel";
import RCAPanel from "../components/dashboard/RCAPanel";
import RecommendationPanel from "../components/dashboard/RecommendationPanel";
import AdvancedTopologyVisualization from "../components/topology/AdvancedTopologyVisualization";
import { api } from "../lib/api";
import { usePlatform, useMetrics, useReasoningLog } from "../contexts/PlatformContext";
import { motion, AnimatePresence } from "framer-motion";
import {
  Server, Zap, ShieldAlert, Cpu, Activity, Network,
  ChevronRight, AlertTriangle, CheckCircle,
} from "lucide-react";

// ── Severity config ──────────────────────────────────────────
const SEV: Record<string, { bar: string; badge: string }> = {
  critical: { bar: "#ef4444", badge: "bg-red-500/15 border border-red-500/30 text-red-400" },
  high:     { bar: "#f97316", badge: "bg-orange-500/15 border border-orange-500/30 text-orange-400" },
  medium:   { bar: "#eab308", badge: "bg-yellow-500/15 border border-yellow-500/30 text-yellow-400" },
  low:      { bar: "#10b981", badge: "bg-green-500/15 border border-green-500/30 text-green-400" },
};

// ── Animated KPI card ────────────────────────────────────────
interface KPICardProps {
  label: string;
  value: string | number;
  sub: string;
  icon: React.ReactNode;
  accentRgb: string;   // "34 211 238"
  i: number;
}
function KPICard({ label, value, sub, icon, accentRgb, i }: KPICardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
      transition={{ delay: i * 0.08 }} whileHover={{ y: -3, transition: { duration: 0.18 } }}
      style={{
        background: `linear-gradient(135deg, rgba(${accentRgb}/0.06) 0%, rgb(11,19,34) 55%)`,
        border: `1px solid rgba(${accentRgb}/0.18)`,
        borderRadius: 12,
        padding: "1.25rem",
        position: "relative",
        overflow: "hidden",
        boxShadow: "0 4px 24px rgba(0,0,0,0.45)",
      }}
    >
      {/* Icon watermark */}
      <div style={{ position: "absolute", top: 14, right: 14, opacity: 0.18, color: `rgb(${accentRgb})` }}>
        {icon}
      </div>
      {/* Label */}
      <p style={{ fontSize: "0.5625rem", fontFamily: "JetBrains Mono", letterSpacing: "0.18em",
        textTransform: "uppercase", color: "rgba(255,255,255,0.35)", marginBottom: 8 }}>
        {label}
      </p>
      {/* Value */}
      <motion.p key={String(value)} initial={{ y: 6, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
        style={{ fontSize: "2rem", fontFamily: "Space Grotesk", fontWeight: 800,
          lineHeight: 1, color: `rgb(${accentRgb})`,
          textShadow: `0 0 18px rgba(${accentRgb}/0.4)` }}>
        {value}
      </motion.p>
      {/* Sub */}
      <p style={{ fontSize: "0.625rem", fontFamily: "JetBrains Mono", color: "rgba(255,255,255,0.3)", marginTop: 8 }}>
        {sub}
      </p>
      {/* Bottom accent line */}
      <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: 1,
        background: `linear-gradient(90deg, transparent, rgba(${accentRgb}/0.45), transparent)` }} />
    </motion.div>
  );
}

export default function Dashboard() {
  const { state, refreshIncidents } = usePlatform();
  const { incidents, topology, health, wsConnected, wsEventCount, criticalCount } = state;
  const metrics   = useMetrics();
  const reasoning = useReasoningLog();

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [rca, setRca]               = useState<Record<string, unknown> | null>(null);
  const [recommendations, setRecommendations] = useState<Awaited<ReturnType<typeof api.recommendations>>>([]);
  const [insights, setInsights]     = useState<Awaited<ReturnType<typeof api.insights>>>([]);
  const [chartData, setChartData]   = useState<{ t: string; ev: number; an: number }[]>([]);
  const tickRef = useRef(0);
  
  useEffect(() => {
    if (!selectedId) return;
    api.rca(selectedId).then(setRca).catch(() => setRca(null));
    api.recommendations(selectedId).then(setRecommendations).catch(() => setRecommendations([]));
    api.insights(selectedId).then(setInsights).catch(() => setInsights([]));
  }, [selectedId]);

  useEffect(() => {
    const build = () => Array.from({ length: 20 }, (_, i) => ({
      t:  i === 19 ? "now" : `-${(19 - i) * 15}s`,
      ev: Math.max(0, wsEventCount + Math.sin(i * 0.6 + tickRef.current * 0.12) * 7 + i * 1.1),
      an: Math.max(0, incidents.length + Math.sin(i * 0.4 + tickRef.current * 0.09) * 3),
    }));
    setChartData(build());
    const t = setInterval(() => { tickRef.current++; setChartData(build()); }, 2200);
    return () => clearInterval(t);
  }, [wsEventCount, incidents.length]);

  // ── KPI definitions ──────────────────────────────────────
  const kpis: KPICardProps[] = [
    { label: "Core Status",       value: health.toUpperCase(),    sub: "All 507 nodes nominal",            icon: <Cpu className="w-5 h-5" />,       accentRgb: health === "healthy" ? "16 185 129" : "239 68 68", i: 0 },
    { label: "Active Incidents",  value: incidents.length,         sub: `${criticalCount} critical · ${incidents.length - criticalCount} others`, icon: <ShieldAlert className="w-5 h-5" />, accentRgb: incidents.length > 0 ? "239 68 68" : "34 211 238", i: 1 },
    { label: "Monitored Nodes",   value: topology?.node_count ?? 507, sub: `${topology?.edge_count ?? 507} neural connections`, icon: <Server className="w-5 h-5" />, accentRgb: "59 130 246", i: 2 },
    { label: "Event Stream",      value: wsEventCount,             sub: `${metrics.p99Latency.toFixed(1)}ms p99 · ${metrics.netMbps.toFixed(0)} Mbps`, icon: <Zap className="w-5 h-5" />, accentRgb: "234 179 8", i: 3 },
  ];

  // ── Panel style helpers ───────────────────────────────────
  const panel = {
    background: "rgb(11,19,34)",
    border: "1px solid rgba(40,65,105,0.35)",
    borderRadius: 12,
    boxShadow: "0 4px 24px rgba(0,0,0,0.45)",
  } as const;

  const panelHeader = {
    display: "flex", alignItems: "center", justifyContent: "space-between",
    padding: "0.75rem 1rem",
    borderBottom: "1px solid rgba(40,65,105,0.3)",
  } as const;

  return (
    <div className="space-y-6 pb-4">
      {/* ── Header ─────────────────────────────────────────── */}
      <header className="flex items-end justify-between">
        <div className="flex items-center gap-4">
          <div style={{ width: 48, height: 48, background: "rgba(34,211,238,0.08)",
            border: "1px solid rgba(34,211,238,0.25)", borderRadius: 12,
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 0 20px rgba(34,211,238,0.1)" }}>
            <Activity className="w-6 h-6 text-sentinel-accent animate-pulse-slow" />
          </div>
          <div>
            <h1 className="page-title glow-text-accent">Operations Center</h1>
            <p className="section-label mt-1">Global Infrastructure Intelligence · Autonomous Monitoring</p>
          </div>
        </div>
        <div style={{
          display: "flex", alignItems: "center", gap: 6,
          padding: "0.5rem 1rem", borderRadius: 10,
          background: wsConnected ? "rgba(16,185,129,0.08)" : "rgba(239,68,68,0.08)",
          border: `1px solid ${wsConnected ? "rgba(16,185,129,0.25)" : "rgba(239,68,68,0.25)"}`,
          fontSize: "0.625rem", fontFamily: "JetBrains Mono", letterSpacing: "0.12em", textTransform: "uppercase",
          color: wsConnected ? "rgb(16,185,129)" : "rgb(239,68,68)",
        }}>
          <span style={{ width: 7, height: 7, borderRadius: "50%",
            background: wsConnected ? "rgb(16,185,129)" : "rgb(239,68,68)",
            ...(wsConnected ? { animation: "pulse-green 2s infinite" } : {}) }} />
          {wsConnected ? "Live Telemetry" : "Reconnecting..."}
        </div>
      </header>

      {/* ── KPI Row ─────────────────────────────────────────── */}
      <div className="grid grid-cols-4 gap-4">
        {kpis.map(card => <KPICard key={card.label} {...card} />)}
      </div>

      {/* ── Main grid ───────────────────────────────────────── */}
      <div className="grid grid-cols-12 gap-5">

        {/* Topology preview — 8 cols */}
        <div className="col-span-8 flex flex-col gap-4">
          <motion.div initial={{ opacity: 0, scale: 0.99 }} animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.15 }} style={{ ...panel, height: 370, position: "relative", overflow: "hidden" }}>
            {/* Header overlay */}
            <div style={{ position: "absolute", top: 0, left: 0, right: 0, zIndex: 10,
              display: "flex", alignItems: "center", justifyContent: "space-between",
              padding: "0.65rem 1rem",
              background: "linear-gradient(to bottom, rgba(6,13,24,0.9) 0%, transparent 100%)" }}>
              <div className="flex items-center gap-2">
                <Network className="w-3.5 h-3.5 text-sentinel-accent" />
                <span style={{ fontSize: "0.5625rem", fontFamily: "JetBrains Mono",
                  letterSpacing: "0.15em", textTransform: "uppercase", color: "rgb(34,211,238)" }}>
                  Neural Map · {topology?.node_count ?? 507} nodes live
                </span>
              </div>
              <Link to="/topology" style={{ fontSize: "0.5rem", fontFamily: "JetBrains Mono",
                letterSpacing: "0.12em", textTransform: "uppercase", color: "rgba(255,255,255,0.3)",
                display: "flex", alignItems: "center", gap: 2 }}
                className="hover:text-sentinel-accent transition-colors">
                Full View <ChevronRight className="w-2.5 h-2.5" />
              </Link>
            </div>
            {topology?.nodes?.length ? (
              <AdvancedTopologyVisualization graph={topology} showPressure={false} showHealth={true}
                showEdgeWeights={false} animateUpdates={true} />
            ) : (
              <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column",
                alignItems: "center", justifyContent: "center", gap: 12 }}>
                <div style={{ width: 28, height: 28, border: "2px solid rgb(34,211,238)",
                  borderTopColor: "transparent", borderRadius: "50%", animation: "spin 1s linear infinite" }} />
                <span style={{ fontSize: "0.5625rem", fontFamily: "JetBrains Mono",
                  letterSpacing: "0.18em", textTransform: "uppercase", color: "rgba(255,255,255,0.28)" }}>
                  Establishing topology uplink...
                </span>
              </div>
            )}
          </motion.div>

          {/* Event velocity chart */}
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }} style={{ ...panel, padding: "1.25rem" }}>
            <div className="flex items-center justify-between mb-4">
              <div>
                <p style={{ fontSize: "0.75rem", fontFamily: "Space Grotesk", fontWeight: 600, color: "#fff" }}>
                  Event Velocity Stream
                </p>
                <p className="section-label mt-0.5">Global telemetry · 20-point rolling window</p>
              </div>
              <div className="flex items-center gap-4" style={{ fontSize: "0.5625rem", fontFamily: "JetBrains Mono" }}>
                <div className="flex items-center gap-1.5" style={{ color: "rgb(34,211,238)" }}>
                  <span style={{ display: "inline-block", width: 10, height: 1, background: "rgb(34,211,238)" }} />Events
                </div>
                <div className="flex items-center gap-1.5" style={{ color: "rgb(239,68,68)" }}>
                  <span style={{ display: "inline-block", width: 10, height: 1, background: "rgb(239,68,68)" }} />Anomalies
                </div>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={110}>
              <AreaChart data={chartData} margin={{ top: 4, right: 0, bottom: 0, left: -30 }}>
                <defs>
                  <linearGradient id="gEv" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#22d3ee" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#22d3ee" stopOpacity={0.02} />
                  </linearGradient>
                  <linearGradient id="gAn" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#ef4444" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="t" stroke="transparent" tick={{ fill: "#334155", fontSize: 8, fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} />
                <YAxis stroke="transparent" tick={{ fill: "#334155", fontSize: 8 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: "#07101e", border: "1px solid rgba(34,211,238,0.2)", borderRadius: 8, fontSize: 10, fontFamily: "JetBrains Mono" }}
                  cursor={{ stroke: "rgba(34,211,238,0.15)", strokeWidth: 1 }} />
                <Area type="monotoneX" dataKey="ev" stroke="#22d3ee" strokeWidth={1.5} fill="url(#gEv)" dot={false} activeDot={{ r: 3, fill: "#22d3ee" }} />
                <Area type="monotoneX" dataKey="an" stroke="#ef4444" strokeWidth={1}   fill="url(#gAn)" dot={false} activeDot={{ r: 3, fill: "#ef4444" }} />
              </AreaChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        {/* Right column — 4 cols */}
        <div className="col-span-4 flex flex-col gap-4">

          {/* Active Incidents */}
          <motion.div initial={{ opacity: 0, x: 18 }} animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }} style={{ ...panel, overflow: "hidden", display: "flex", flexDirection: "column" }}>
            <div style={panelHeader}>
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
                <span style={{ fontSize: "0.6875rem", fontFamily: "Space Grotesk", fontWeight: 700, color: "#fff" }}>
                  Active Anomalies
                </span>
              </div>
              <div className="flex items-center gap-2">
                {criticalCount > 0 && (
                  <span style={{ fontSize: "0.5rem", fontFamily: "JetBrains Mono", letterSpacing: "0.1em", textTransform: "uppercase",
                    padding: "2px 7px", borderRadius: 20, background: "rgba(239,68,68,0.12)",
                    border: "1px solid rgba(239,68,68,0.3)", color: "rgb(239,68,68)" }}
                    className="animate-pulse">
                    {criticalCount} critical
                  </span>
                )}
                <Link to="/incidents" style={{ fontSize: "0.5rem", fontFamily: "JetBrains Mono",
                  color: "rgba(255,255,255,0.25)", letterSpacing: "0.1em", textTransform: "uppercase" }}
                  className="hover:text-sentinel-accent transition-colors">
                  All →
                </Link>
              </div>
            </div>

            <div style={{ overflowY: "auto", maxHeight: 260 }}>
              <AnimatePresence mode="popLayout">
                {incidents.slice(0, 7).map((inc) => {
                  const s = SEV[inc.severity] ?? SEV.low;
                  return (
                    <motion.button key={inc.id}
                      layout
                      initial={{ opacity: 0, x: -15, scale: 0.98 }} 
                      animate={{ opacity: 1, x: 0, scale: 1 }} 
                      exit={{ opacity: 0, height: 0, x: -15, scale: 0.98 }}
                      transition={{ type: "spring", stiffness: 400, damping: 25 }}
                      onClick={() => setSelectedId(inc.id)}
                      style={{
                        width: "100%", textAlign: "left",
                        padding: "0.75rem 1rem",
                        borderLeft: `2px solid ${s.bar}`,
                        borderBottom: "1px solid rgba(40,65,105,0.2)",
                        background: selectedId === inc.id ? "rgba(255,255,255,0.03)" : "transparent",
                        transition: "background 0.15s",
                      }}
                      className="hover:bg-white/[0.02]">
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
                        <span style={{ fontSize: "0.5rem", fontFamily: "JetBrains Mono", letterSpacing: "0.12em", textTransform: "uppercase",
                          padding: "1px 6px", borderRadius: 4, ...{ className: s.badge } }}
                          className={s.badge}>
                          {inc.severity}
                        </span>
                        <span style={{ fontSize: "0.5625rem", fontFamily: "JetBrains Mono", color: "rgba(255,255,255,0.22)" }}>
                          {new Date(inc.started_at).toLocaleTimeString()}
                        </span>
                      </div>
                      <Link to={`/incidents/${inc.id}`}
                        style={{ fontSize: "0.6875rem", fontFamily: "Space Grotesk", color: "rgba(255,255,255,0.72)",
                          lineHeight: 1.4, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}
                        className="hover:text-white transition-colors">
                        {inc.title}
                      </Link>
                    </motion.button>
                  );
                })}
              </AnimatePresence>
              {incidents.length === 0 && (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "3rem 1rem", gap: 10 }}>
                  <CheckCircle className="w-7 h-7 text-sentinel-success" style={{ opacity: 0.4 }} />
                  <p className="section-label">All systems nominal</p>
                </div>
              )}
            </div>
          </motion.div>

          {/* AI Cognitive Stream */}
          <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.28 }}
            style={{ ...panel, border: "1px solid rgba(34,211,238,0.12)", overflow: "hidden" }}>
            <div style={panelHeader}>
              <div className="flex items-center gap-2">
                <span style={{ width: 7, height: 7, borderRadius: "50%", background: "rgb(34,211,238)", animation: "pulse-green 2s infinite", display: "inline-block" }} />
                <span style={{ fontSize: "0.6875rem", fontFamily: "Space Grotesk", fontWeight: 700, color: "#fff" }}>
                  AI Cognitive Stream
                </span>
              </div>
              <span style={{ fontSize: "0.5rem", fontFamily: "JetBrains Mono", color: "rgba(255,255,255,0.22)" }}>
                {reasoning.length} signals
              </span>
            </div>
            <div style={{ padding: "0.5rem 0.75rem", maxHeight: 140, overflow: "hidden", position: "relative" }}>
              <div style={{ position: "absolute", inset: "0 0 0 0", bottom: 0, left: 0, right: 0, height: 36,
                background: "linear-gradient(to top, rgb(11,19,34), transparent)", zIndex: 10, pointerEvents: "none" }} />
              <AnimatePresence mode="popLayout">
                {reasoning.slice(0, 5).map(r => (
                  <motion.div key={r.id} 
                    layout
                    initial={{ opacity: 0, x: -10 }} 
                    animate={{ opacity: 1, x: 0 }} 
                    exit={{ opacity: 0, filter: "blur(4px)" }}
                    transition={{ type: "spring", stiffness: 350, damping: 25 }}
                    className={`terminal-line ${r.kind === "critical" ? "!text-red-400 !border-l-red-500/50" : r.kind === "success" ? "!text-green-400 !border-l-green-500/50" : r.kind === "warn" ? "!text-yellow-400 !border-l-yellow-500/50" : ""}`}
                    style={{ marginBottom: 4 }}>
                    <span className="ts">[{r.agent}]</span> {r.text}
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </motion.div>

          {/* RCA */}
          <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}>
            <RCAPanel rca={rca} />
          </motion.div>
        </div>
      </div>

      {/* ── Bottom row ──────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-5">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
          <AIInsightsPanel insights={insights as any} wsEvents={[]} />
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }}>
          <RecommendationPanel items={recommendations} />
        </motion.div>
      </div>
    </div>
  );
}
