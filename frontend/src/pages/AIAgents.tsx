import React, { useEffect, useState, useRef, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { usePlatform, useReasoningLog, useAgentActivity, type ReasoningEntry } from "../contexts/PlatformContext";
import {
  Brain, Cpu, Zap, Activity, CheckCircle2, Clock, AlertTriangle,
  RefreshCw, Wifi, BarChart3, GitBranch, TrendingUp
} from "lucide-react";

const AGENTS = [
  { id: "rca",            name: "RCA Engine",      icon: <Brain className="w-4 h-4" />,       color: "text-purple-400",  border: "border-purple-500/30",  bg: "rgba(168,85,247,0.06)",   role: "Root Cause Analysis",    model: "llama3.2:3b" },
  { id: "cpu",            name: "CPU Monitor",     icon: <Cpu className="w-4 h-4" />,         color: "text-red-400",     border: "border-red-500/30",     bg: "rgba(239,68,68,0.06)",    role: "Resource Analysis",      model: "mistral:7b"  },
  { id: "correlation",   name: "Correlator",      icon: <GitBranch className="w-4 h-4" />,   color: "text-yellow-400",  border: "border-yellow-500/30",  bg: "rgba(234,179,8,0.06)",    role: "Event Correlation",      model: "llama3.2:3b" },
  { id: "recommendation",name: "Recommender",     icon: <Zap className="w-4 h-4" />,         color: "text-cyan-400",    border: "border-cyan-500/30",    bg: "rgba(34,211,238,0.06)",   role: "Action Planning",        model: "mistral:7b"  },
  { id: "memory",        name: "Memory Agent",    icon: <Activity className="w-4 h-4" />,    color: "text-orange-400",  border: "border-orange-500/30",  bg: "rgba(249,115,22,0.06)",   role: "Memory Pressure",        model: "llama3.2:3b" },
  { id: "network",       name: "Network Monitor", icon: <Wifi className="w-4 h-4" />,        color: "text-blue-400",    border: "border-blue-500/30",    bg: "rgba(59,130,246,0.06)",   role: "Latency Tracking",       model: "mistral:7b"  },
  { id: "summarization", name: "Summarizer",      icon: <BarChart3 className="w-4 h-4" />,   color: "text-green-400",   border: "border-green-500/30",   bg: "rgba(16,185,129,0.06)",   role: "Incident Summarization", model: "llama3.2:3b" },
];

/** Compact scrollable log — fixed height, append-only, no layout refresh animations */
function LiveReasoningStream({ entries }: { entries: ReasoningEntry[] }) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const prevLenRef = useRef(0);

  const chronological = useMemo(
    () => [...entries].reverse(),
    [entries]
  );

  useEffect(() => {
    const el = scrollRef.current;
    if (!el || entries.length === prevLenRef.current) return;
    prevLenRef.current = entries.length;
    el.scrollTop = el.scrollHeight;
  }, [entries.length, chronological]);

  return (
    <div
      className="glass-panel rounded-xl border border-sentinel-accent/15 flex flex-col shrink-0"
      style={{ height: 400 }}
    >
      <div className="px-4 py-2.5 border-b border-sentinel-700/40 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-sentinel-accent animate-pulse" />
          <span className="text-xs font-display font-semibold text-white">Live Reasoning Stream</span>
        </div>
        <span className="text-[9px] font-mono text-gray-500 tabular-nums">{entries.length} signals</span>
      </div>
      <div
        ref={scrollRef}
        className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-2.5 space-y-1 scrollbar-thin scrollbar-thumb-cyan-500/20 scrollbar-track-transparent"
      >
        {chronological.length === 0 ? (
          <p className="text-center text-gray-700 text-[9px] font-mono uppercase tracking-widest py-6">
            Waiting for agent signals...
          </p>
        ) : (
          chronological.map((r) => (
            <div
              key={r.id}
              className={`terminal-line text-[9px] leading-relaxed shrink-0 ${
                r.kind === "critical"
                  ? "!border-red-500/50 !text-red-400"
                  : r.kind === "success"
                    ? "!border-green-500/50 !text-green-400"
                    : r.kind === "warn"
                      ? "!border-yellow-500/50 !text-yellow-400"
                      : ""
              }`}
            >
              <span className="ts">[{r.ts}]</span>{" "}
              <span className="opacity-60 mr-1">[{r.agent}]</span>
              {r.text}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: "idle" | "active" | "thinking" | undefined }) {
  if (!status || status === "idle") {
    return <span className="text-[8px] font-mono uppercase tracking-widest px-2 py-0.5 rounded-full bg-gray-800 text-gray-500 border border-gray-700/50">● IDLE</span>;
  }
  if (status === "thinking") {
    return <span className="text-[8px] font-mono uppercase tracking-widest px-2 py-0.5 rounded-full bg-yellow-500/10 text-yellow-400 border border-yellow-500/30 animate-pulse">◎ THINKING</span>;
  }
  return <span className="text-[8px] font-mono uppercase tracking-widest px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 border border-green-500/30">● ACTIVE</span>;
}

export default function AIAgents() {
  const { state } = usePlatform();
  const reasoning = useReasoningLog();
  const agentActivity = useAgentActivity();

  // Persistent per-agent metrics (drift from initial, no full reset on nav)
  const [agentMetrics, setAgentMetrics] = useState<Record<string, { conf: number; calls: number; latency: number; acc: number }>>(() =>
    Object.fromEntries(AGENTS.map(a => [a.id, { conf: 70 + Math.random() * 25, calls: Math.floor(Math.random() * 150), latency: 1.5 + Math.random() * 2, acc: 75 + Math.random() * 20 }]))
  );

  // Drift agent metrics over time (no reinit)
  useEffect(() => {
    const t = setInterval(() => {
      setAgentMetrics(prev => {
        const next = { ...prev };
        AGENTS.forEach(a => {
          const m = next[a.id];
          next[a.id] = {
            conf:    Math.max(50, Math.min(99,  m.conf    + (Math.random() - 0.45) * 3)),
            calls:   m.calls + Math.floor(Math.random() * 3),
            latency: Math.max(0.4, Math.min(5,  m.latency + (Math.random() - 0.5) * 0.3)),
            acc:     Math.max(60, Math.min(99,  m.acc     + (Math.random() - 0.4) * 2)),
          };
        });
        return next;
      });
    }, 3000);
    return () => clearInterval(t);
  }, []);

  // Agent-specific reasoning lines
  const agentReasoningMap = React.useMemo(() => {
    const map: Record<string, typeof reasoning> = {};
    AGENTS.forEach(a => {
      map[a.id] = reasoning.filter(r => r.agent.toLowerCase().includes(a.name.split(" ")[0].toLowerCase())).slice(0, 3);
    });
    return map;
  }, [reasoning]);

  return (
    <div className="h-full flex flex-col gap-5">
      {/* Header */}
      <header className="flex items-end justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-purple-500/10 border border-purple-500/30 rounded-xl flex items-center justify-center shadow-[0_0_25px_rgba(168,85,247,0.2)]">
            <Brain className="w-6 h-6 text-purple-400 animate-pulse-slow" />
          </div>
          <div>
            <h1 className="page-title glow-text-purple">AI Agent Network</h1>
            <p className="text-[10px] font-mono text-gray-500 uppercase tracking-widest mt-1">
              Multi-agent Ollama orchestration · Local inference · {AGENTS.length} agents online
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="glass-panel border border-purple-500/20 rounded-xl px-4 py-2 flex items-center gap-3">
            <div>
              <div className="text-[8px] font-mono text-gray-500 uppercase tracking-widest">GPU Util</div>
              <div className="flex items-center gap-2 mt-0.5">
                <div className="w-20 h-1.5 bg-black/50 rounded-full overflow-hidden">
                  <motion.div className="h-full rounded-full bg-gradient-to-r from-purple-500 to-cyan-400"
                    animate={{ width: `${state.gpuUtil}%` }} transition={{ duration: 1 }} />
                </div>
                <span className="text-xs font-display font-bold text-purple-400">{state.gpuUtil.toFixed(0)}%</span>
              </div>
            </div>
            <div className="w-px h-8 bg-gray-800" />
            <div className={`flex items-center gap-1.5 text-[9px] font-mono uppercase tracking-widest ${state.wsConnected ? "text-green-400" : "text-gray-500"}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${state.wsConnected ? "bg-green-400 animate-pulse" : "bg-gray-600"}`} />
              Ollama {state.wsConnected ? "Online" : "Offline"}
            </div>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-12 gap-5 flex-1 min-h-0">
        {/* Agent cards — 7 cols */}
        <div className="col-span-7 grid grid-cols-2 gap-3 content-start overflow-y-auto pr-1">
          <AnimatePresence>
            {AGENTS.map((agent, i) => {
              const m = agentMetrics[agent.id] ?? { conf: 80, calls: 0, latency: 2, acc: 80 };
              const status = agentActivity[agent.id];
              return (
                <motion.div
                  key={agent.id}
                  initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.06 }}
                  className={`glass-panel rounded-xl border ${agent.border} p-4 relative overflow-hidden holo-card`}
                  style={{ background: `linear-gradient(135deg, ${agent.bg} 0%, transparent 60%)` }}
                >
                  {/* Status badge top-right */}
                  <div className="absolute top-3 right-3">
                    <StatusBadge status={status} />
                  </div>

                  {/* Agent header */}
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`w-8 h-8 rounded-lg bg-black/40 border ${agent.border} flex items-center justify-center ${agent.color}`}>
                      {agent.icon}
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-display font-bold text-white">{agent.name}</p>
                      <p className="text-[8px] font-mono text-gray-600 uppercase tracking-widest">{agent.role}</p>
                    </div>
                  </div>

                  {/* Metrics row */}
                  <div className="grid grid-cols-3 gap-2 mb-3">
                    {[
                      { label: "Confidence", value: `${m.conf.toFixed(0)}%`, color: m.conf > 85 ? "text-green-400" : m.conf > 70 ? agent.color : "text-red-400" },
                      { label: "API Calls",  value: m.calls,                 color: agent.color },
                      { label: "Latency",    value: `${m.latency.toFixed(1)}s`, color: m.latency > 3 ? "text-orange-400" : "text-sentinel-accent" },
                    ].map(metric => (
                      <div key={metric.label} className="text-center bg-black/25 rounded-lg p-1.5">
                        <motion.p key={String(metric.value)} initial={{ y: 4, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
                          className={`text-sm font-display font-black tabular-nums ${metric.color}`}>
                          {metric.value}
                        </motion.p>
                        <p className="text-[7px] font-mono text-gray-600 uppercase tracking-widest mt-0.5">{metric.label}</p>
                      </div>
                    ))}
                  </div>

                  {/* Accuracy bar */}
                  <div>
                    <div className="flex items-center justify-between text-[8px] font-mono text-gray-600 mb-1">
                      <span>Inference Accuracy</span>
                      <span className={agent.color}>{m.acc.toFixed(1)}%</span>
                    </div>
                    <div className="h-1 bg-black/50 rounded-full overflow-hidden">
                      <motion.div className={`h-full rounded-full`}
                        style={{ background: `linear-gradient(90deg, ${agent.color.replace("text-", "").replace("-400", "")} transparent)` }}
                        animate={{ width: `${m.acc}%` }} transition={{ duration: 0.8 }}>
                        <div className="h-full rounded-full bg-current opacity-80" />
                      </motion.div>
                    </div>
                  </div>

                  {/* Model tag */}
                  <div className="mt-2.5 flex items-center justify-between">
                    <span className="text-[8px] font-mono text-gray-700 uppercase tracking-widest">Model</span>
                    <span className={`text-[8px] font-mono ${agent.color} opacity-70`}>{agent.model}</span>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>

        {/* Right — metrics + compact reasoning stream */}
        <div className="col-span-5 flex flex-col gap-3 shrink-0">
          {/* System Metrics */}
          <div className="glass-panel rounded-xl border border-sentinel-700/40 p-4">
            <p className="text-[9px] font-mono text-gray-500 uppercase tracking-widest mb-3">System Performance</p>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "CPU Avg",   value: `${state.metrics.cpuAvg.toFixed(0)}%`,         color: "text-red-400",     bar: state.metrics.cpuAvg },
                { label: "Mem Usage", value: `${state.metrics.memUsage.toFixed(0)}%`,        color: "text-orange-400",  bar: state.metrics.memUsage },
                { label: "Net I/O",   value: `${state.metrics.netMbps.toFixed(0)} Mbps`,     color: "text-blue-400",    bar: state.metrics.netMbps / 20 },
                { label: "SLA",       value: `${state.metrics.slaPercent.toFixed(1)}%`,      color: "text-green-400",   bar: state.metrics.slaPercent },
              ].map(m => (
                <div key={m.label} className="bg-black/30 rounded-lg p-2.5">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[8px] font-mono text-gray-600 uppercase">{m.label}</span>
                    <motion.span key={m.value} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className={`text-xs font-display font-bold ${m.color}`}>
                      {m.value}
                    </motion.span>
                  </div>
                  <div className="h-1 bg-black/50 rounded-full overflow-hidden">
                    <motion.div className="h-full rounded-full bg-current" style={{ color: m.color.replace("text-", "") }}
                      animate={{ width: `${Math.min(100, m.bar)}%` }} transition={{ duration: 1 }}>
                      <div className="h-full w-full bg-current opacity-80 rounded-full" />
                    </motion.div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <LiveReasoningStream entries={reasoning} />
        </div>
      </div>
    </div>
  );
}
