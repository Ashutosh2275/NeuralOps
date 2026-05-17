import React, { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useWebSocket } from "../hooks/useWebSocket";
import { api } from "../lib/api";
import {
  Brain, Cpu, Zap, Activity, CheckCircle2, Clock, AlertTriangle,
  ChevronRight, RefreshCw, Wifi, BarChart3, GitBranch
} from "lucide-react";

// ── Synthetic agent data for always-populated UI ──────────────
const AGENTS = [
  { id: "rca",            name: "RCA Engine",        icon: <Brain className="w-4 h-4" />,      color: "text-purple-400",  border: "border-purple-500/30", role: "Root Cause Analysis",      model: "llama3.2:3b" },
  { id: "cpu",            name: "CPU Monitor",       icon: <Cpu className="w-4 h-4" />,        color: "text-red-400",     border: "border-red-500/30",    role: "Resource Analysis",        model: "mistral:7b"  },
  { id: "correlation",   name: "Correlator",        icon: <GitBranch className="w-4 h-4" />,  color: "text-yellow-400",  border: "border-yellow-500/30", role: "Event Correlation",        model: "llama3.2:3b" },
  { id: "recommendation",name: "Recommender",       icon: <Zap className="w-4 h-4" />,        color: "text-cyan-400",    border: "border-cyan-500/30",   role: "Action Planning",          model: "mistral:7b"  },
  { id: "memory",        name: "Memory Agent",      icon: <Activity className="w-4 h-4" />,   color: "text-orange-400",  border: "border-orange-500/30", role: "Memory Pressure",          model: "llama3.2:3b" },
  { id: "network",       name: "Network Monitor",   icon: <Wifi className="w-4 h-4" />,       color: "text-blue-400",    border: "border-blue-500/30",   role: "Latency Tracking",         model: "mistral:7b"  },
  { id: "summarization", name: "Summarizer",        icon: <BarChart3 className="w-4 h-4" />,  color: "text-green-400",   border: "border-green-500/30",  role: "Incident Summarization",   model: "llama3.2:3b" },
];

const REASONING_SEEDS = [
  "Analyzing memory pressure pattern across payment-service replicas...",
  "Cross-referencing pod restart timestamps with network latency spikes...",
  "Confidence threshold met. Correlating OOMKill events with TCP timeout chain...",
  "Blast radius estimation: 4 downstream services within propagation depth 3...",
  "Generating autonomous remediation strategy with 94% success probability...",
  "Validating replica scale-up feasibility against cluster resource quota...",
  "Emitting recommendation: `kubectl rollout restart deploy/payment-service`",
  "Health propagation mapped. api-gateway degraded → auth-service timeout...",
  "Multi-agent consensus: root cause confirmed. Triggering autonomous patch...",
  "GPU inference complete. RTX 3050 Ti at 78% utilisation. Latency 1.2s...",
];

export default function AIAgentsPage() {
  const { events, connected } = useWebSocket();
  const [reasoningLog, setReasoningLog] = useState<string[]>([]);
  const [agentStats, setAgentStats] = useState<Record<string, { conf: number; calls: number; latency: number; status: "active"|"idle"|"thinking" }>>({});
  const [gpuUtil, setGpuUtil] = useState(72);
  const [incidents, setIncidents] = useState<any[]>([]);
  const logRef = useRef<HTMLDivElement>(null);
  const seedIdx = useRef(0);

  // Seed agent stats
  useEffect(() => {
    const stats: typeof agentStats = {};
    AGENTS.forEach(a => {
      stats[a.id] = { conf: 70 + Math.random() * 28, calls: Math.floor(Math.random() * 120) + 20, latency: 0.8 + Math.random() * 2.5, status: "idle" };
    });
    setAgentStats(stats);
    api.incidents().then(setIncidents).catch(() => {});
  }, []);

  // Auto-stream reasoning messages
  useEffect(() => {
    const t = setInterval(() => {
      const msg = REASONING_SEEDS[seedIdx.current % REASONING_SEEDS.length];
      seedIdx.current++;
      setReasoningLog(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev].slice(0, 60));
      
      // Randomly activate an agent
      const agent = AGENTS[Math.floor(Math.random() * AGENTS.length)];
      setAgentStats(prev => ({
        ...prev,
        [agent.id]: { ...prev[agent.id], status: "thinking", conf: 70 + Math.random() * 28, calls: (prev[agent.id]?.calls ?? 0) + 1, latency: 0.8 + Math.random() * 2.5 },
      }));
      setGpuUtil(65 + Math.random() * 25);

      setTimeout(() => {
        setAgentStats(prev => ({
          ...prev,
          [agent.id]: { ...prev[agent.id], status: Math.random() > 0.3 ? "active" : "idle" },
        }));
      }, 2000);
    }, 2800);
    return () => clearInterval(t);
  }, []);

  // Also push WS events to log
  useEffect(() => {
    if (!events.length) return;
    const e = events[0];
    if (e.type === "ai_insight") {
      const agent = String(e.payload?.agent ?? "rca");
      const finding = String((e.payload?.findings as any)?.[0] ?? "");
      if (finding) setReasoningLog(prev => [`[${new Date().toLocaleTimeString()}] [${agent.toUpperCase()}] ${finding}`, ...prev].slice(0, 60));
    }
  }, [events]);

  useEffect(() => { logRef.current?.scrollTo({ top: 0, behavior: "smooth" }); }, [reasoningLog.length]);

  return (
    <div className="h-full flex flex-col gap-6">
      {/* Header */}
      <header className="flex items-end justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-purple-500/10 border border-purple-500/30 rounded-xl flex items-center justify-center shadow-[0_0_25px_rgba(168,85,247,0.25)]">
            <Brain className="w-6 h-6 text-purple-400 animate-pulse-slow" />
          </div>
          <div>
            <h1 className="page-title glow-text-accent" style={{ textShadow: "0 0 20px rgba(168,85,247,0.5)" }}>AI Agent Network</h1>
            <p className="text-[10px] font-mono text-gray-500 uppercase tracking-widest mt-1">Multi-Agent Ollama Orchestration · Local Inference</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="glass-panel px-4 py-2 rounded-lg flex items-center gap-3 border border-purple-500/20">
            <div className="flex flex-col">
              <span className="text-[9px] font-mono text-gray-500 uppercase tracking-widest">GPU Util</span>
              <div className="flex items-center gap-2 mt-0.5">
                <div className="w-24 h-1.5 bg-sentinel-800 rounded-full overflow-hidden">
                  <motion.div className="h-full rounded-full bg-purple-500" animate={{ width: `${gpuUtil}%` }} transition={{ duration: 1 }} style={{ boxShadow: "0 0 8px rgba(168,85,247,0.8)" }} />
                </div>
                <span className="text-xs font-mono text-purple-400 tabular-nums">{gpuUtil.toFixed(0)}%</span>
              </div>
            </div>
          </div>
          <div className={`flex items-center gap-2 text-[10px] font-mono uppercase tracking-widest px-4 py-2 rounded-lg glass-panel border ${connected ? "border-sentinel-success/30 text-sentinel-success" : "border-sentinel-danger/30 text-sentinel-danger"}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${connected ? "bg-sentinel-success animate-pulse" : "bg-sentinel-danger"}`} />
            {connected ? "OLLAMA ONLINE" : "OFFLINE"}
          </div>
        </div>
      </header>

      <div className="grid grid-cols-12 gap-6 flex-1 min-h-0">
        {/* Agent Cards — left 8 cols */}
        <div className="col-span-8 grid grid-cols-2 gap-4 content-start overflow-y-auto pr-1">
          {AGENTS.map((agent, i) => {
            const stats = agentStats[agent.id] ?? { conf: 85, calls: 45, latency: 1.2, status: "idle" as const };
            return (
              <motion.div
                key={agent.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.07 }}
                className={`glass-panel rounded-xl border ${agent.border} p-4 hover:scale-[1.01] transition-transform duration-200 group`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className={`w-9 h-9 rounded-lg border ${agent.border} bg-black/40 flex items-center justify-center ${agent.color}`}>
                      {agent.icon}
                    </div>
                    <div>
                      <h3 className="text-sm font-display font-semibold text-white">{agent.name}</h3>
                      <p className="text-[9px] font-mono text-gray-500 uppercase tracking-widest mt-0.5">{agent.role}</p>
                    </div>
                  </div>
                  <div className={`flex items-center gap-1.5 text-[9px] font-mono uppercase px-2 py-0.5 rounded border ${
                    stats.status === "thinking" ? "border-yellow-500/40 bg-yellow-500/10 text-yellow-400 animate-pulse" :
                    stats.status === "active"   ? "border-green-500/40 bg-green-500/10 text-green-400" :
                                                  "border-gray-700/50 bg-gray-800/40 text-gray-500"
                  }`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${stats.status === "thinking" ? "bg-yellow-400" : stats.status === "active" ? "bg-green-400" : "bg-gray-600"}`} />
                    {stats.status}
                  </div>
                </div>

                {/* Stats row */}
                <div className="grid grid-cols-3 gap-2 mb-3">
                  {[
                    { label: "Confidence", val: `${stats.conf.toFixed(0)}%`, color: stats.conf > 80 ? "text-green-400" : stats.conf > 65 ? "text-yellow-400" : "text-red-400" },
                    { label: "API Calls",  val: stats.calls,                color: "text-sentinel-accent" },
                    { label: "Latency",    val: `${stats.latency.toFixed(1)}s`, color: "text-orange-400" },
                  ].map(({ label, val, color }) => (
                    <div key={label} className="bg-black/30 rounded-lg p-2 text-center">
                      <p className={`text-sm font-display font-bold ${color} tabular-nums`}>{val}</p>
                      <p className="text-[8px] font-mono text-gray-600 uppercase tracking-widest mt-0.5">{label}</p>
                    </div>
                  ))}
                </div>

                {/* Confidence bar */}
                <div className="space-y-1">
                  <div className="flex justify-between text-[9px] font-mono text-gray-600 uppercase tracking-widest">
                    <span>Inference Accuracy</span>
                    <span className={agent.color}>{stats.conf.toFixed(1)}%</span>
                  </div>
                  <div className="h-1 bg-sentinel-900 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full rounded-full"
                      animate={{ width: `${stats.conf}%` }}
                      transition={{ duration: 0.8, ease: "easeOut" }}
                      style={{ background: stats.conf > 80 ? "#10b981" : stats.conf > 65 ? "#f59e0b" : "#ef4444", boxShadow: "0 0 6px currentColor" }}
                    />
                  </div>
                </div>

                <div className="mt-2 pt-2 border-t border-sentinel-700/30 flex items-center justify-between">
                  <span className="text-[9px] font-mono text-gray-600 uppercase tracking-widest">Model</span>
                  <code className="text-[9px] font-mono text-sentinel-accent/70">{agent.model}</code>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Right — Reasoning stream */}
        <div className="col-span-4 flex flex-col gap-4 h-full overflow-hidden">
          <div className="glass-panel rounded-xl border border-purple-500/25 flex flex-col flex-1 overflow-hidden">
            <div className="px-4 py-3 border-b border-sentinel-700/40 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-purple-400 animate-ping" />
                <span className="text-xs font-display font-semibold text-white">Live Reasoning Stream</span>
              </div>
              <span className="text-[9px] font-mono text-gray-500 uppercase tracking-widest">{reasoningLog.length} messages</span>
            </div>
            <div ref={logRef} className="flex-1 overflow-y-auto p-3 space-y-1.5">
              <AnimatePresence mode="popLayout">
                {reasoningLog.map((line, i) => {
                  const isGPU = line.includes("GPU");
                  const isError = line.includes("CRITICAL") || line.includes("blast");
                  const isSuccess = line.includes("complete") || line.includes("confirmed");
                  return (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: -8, scale: 0.98 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0 }}
                      className={`terminal-line text-[10px] leading-relaxed ${isError ? "!border-red-500/50 !text-red-400" : isSuccess ? "!border-green-500/50 !text-green-400" : isGPU ? "!border-purple-500/50 !text-purple-400" : ""}`}
                    >
                      {line}
                    </motion.div>
                  );
                })}
              </AnimatePresence>
              {reasoningLog.length === 0 && (
                <div className="text-center py-12 text-gray-600 font-mono text-xs uppercase tracking-widest animate-pulse">
                  Initializing AI agents...
                </div>
              )}
            </div>
          </div>

          {/* GPU stats box */}
          <div className="glass-panel rounded-xl border border-purple-500/20 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Cpu className="w-4 h-4 text-purple-400" />
              <span className="text-xs font-display font-semibold text-white">RTX 3050 Ti · Local Inference</span>
            </div>
            <div className="space-y-2">
              {[["GPU Utilisation", gpuUtil, "bg-purple-500", "rgba(168,85,247,0.8)"],
                ["VRAM Usage",    62,       "bg-blue-500",   "rgba(59,130,246,0.8)"],
                ["Temp",          71,       "bg-orange-500", "rgba(249,115,22,0.8)"],
              ].map(([label, val, cls, glow]) => (
                <div key={label as string} className="space-y-0.5">
                  <div className="flex justify-between text-[9px] font-mono text-gray-500 uppercase tracking-widest">
                    <span>{label as string}</span>
                    <span className="text-gray-300 tabular-nums">{Number(val).toFixed(0)}{label === "Temp" ? "°C" : "%"}</span>
                  </div>
                  <div className="h-1 bg-sentinel-900 rounded-full overflow-hidden">
                    <motion.div className={`h-full rounded-full ${cls as string}`} animate={{ width: `${val}%` }} transition={{ duration: 1 }} style={{ boxShadow: `0 0 6px ${glow}` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
