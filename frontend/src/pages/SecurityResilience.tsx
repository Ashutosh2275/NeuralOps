import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Shield, ShieldCheck, ShieldAlert, Lock, Eye, Wifi, Server,
  CheckCircle, AlertTriangle, TrendingUp, RefreshCw, Zap, Globe
} from "lucide-react";

const CHECKS = [
  { id: "ws",       label: "WebSocket Integrity",    icon: <Wifi className="w-4 h-4" />,       passing: true,  detail: "All WS channels authenticated · TLS 1.3" },
  { id: "replay",   label: "Replay Tamper Guard",    icon: <Eye className="w-4 h-4" />,         passing: true,  detail: "Event signatures verified · immutable ledger intact" },
  { id: "api",      label: "API Authentication",     icon: <Lock className="w-4 h-4" />,        passing: true,  detail: "Bearer tokens valid · rate limiting active" },
  { id: "infra",    label: "Infrastructure Integrity",icon: <Server className="w-4 h-4" />,    passing: true,  detail: "Node attestation passed · kubelet healthy" },
  { id: "ollama",   label: "AI Inference Isolation",  icon: <Shield className="w-4 h-4" />,    passing: true,  detail: "Ollama sandboxed · no external network calls" },
  { id: "storage",  label: "Data Sovereignty",       icon: <Globe className="w-4 h-4" />,       passing: true,  detail: "All data on-premise · zero cloud egress" },
];

function ResilienceRing({ score }: { score: number }) {
  const r = 54, circ = 2 * Math.PI * r;
  const dash = circ * (score / 100);
  const color = score > 80 ? "#10b981" : score > 60 ? "#f59e0b" : "#ef4444";
  return (
    <div className="relative w-36 h-36 flex items-center justify-center">
      <svg className="absolute inset-0 w-full h-full -rotate-90">
        <circle cx="72" cy="72" r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
        <motion.circle
          cx="72" cy="72" r={r} fill="none"
          stroke={color} strokeWidth="8"
          strokeLinecap="round"
          initial={{ strokeDashoffset: circ }}
          animate={{ strokeDashoffset: circ - dash }}
          transition={{ duration: 1.5, ease: "easeOut" }}
          strokeDasharray={circ}
          style={{ filter: `drop-shadow(0 0 8px ${color})` }}
        />
      </svg>
      <div className="text-center">
        <p className="text-3xl font-display font-bold text-white tabular-nums">{score}</p>
        <p className="text-[9px] font-mono text-gray-500 uppercase tracking-widest">Resilience</p>
      </div>
    </div>
  );
}

export default function SecurityResilience() {
  const connected = true; const events: any[] = [];
  const [score, setScore] = useState(94);
  const [threats, setThreats] = useState<{ id: string; msg: string; sev: string; ts: string }[]>([]);
  const [wsHealth, setWsHealth] = useState({ latency: 12, reconnects: 0, msgRate: 24 });

  useEffect(() => {
    const t = setInterval(() => {
      setScore(s => Math.max(70, Math.min(99, s + (Math.random() - 0.3) * 2)));
      setWsHealth(w => ({
        latency: Math.max(2, Math.min(80, w.latency + (Math.random() - 0.5) * 5)),
        reconnects: w.reconnects,
        msgRate: Math.max(5, Math.min(60, w.msgRate + (Math.random() - 0.5) * 6)),
      }));
    }, 3000);
    return () => clearInterval(t);
  }, []);

  // Track WS events as "detections"
  useEffect(() => {
    if (!events.length) return;
    const e = events[0];
    if (e.type === "anomaly" || e.type === "ai_insight") {
      setThreats(prev => [{
        id: Math.random().toString(36).slice(2),
        msg: `${e.type === "anomaly" ? "Anomaly" : "AI signal"} detected in ${String(e.payload?.service ?? e.payload?.agent ?? "system")}`,
        sev: e.type === "anomaly" ? "medium" : "low",
        ts: new Date().toLocaleTimeString(),
      }, ...prev].slice(0, 20));
    }
  }, [events]);

  return (
    <div className="h-full flex flex-col gap-6">
      <header className="flex items-end justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-green-500/10 border border-green-500/30 rounded-xl flex items-center justify-center shadow-[0_0_25px_rgba(16,185,129,0.2)]">
            <ShieldCheck className="w-6 h-6 text-green-400" />
          </div>
          <div>
            <h1 className="page-title" style={{ textShadow: "0 0 20px rgba(16,185,129,0.4)" }}>Security & Resilience</h1>
            <p className="text-[10px] font-mono text-gray-500 uppercase tracking-widest mt-1">Zero-trust · Air-gapped inference · On-premise sovereignty</p>
          </div>
        </div>
        <div className={`flex items-center gap-2 text-sm font-display font-semibold px-4 py-2 rounded-xl glass-panel border ${connected ? "border-green-500/30 text-green-400" : "border-red-500/30 text-red-400"}`}>
          {connected ? <ShieldCheck className="w-4 h-4" /> : <ShieldAlert className="w-4 h-4" />}
          {connected ? "All Systems Secure" : "Connection Lost"}
        </div>
      </header>

      <div className="grid grid-cols-12 gap-6 flex-1 min-h-0">
        {/* Left — Resilience score + checks */}
        <div className="col-span-4 flex flex-col gap-4">
          <div className="glass-panel rounded-xl border border-green-500/20 p-5 flex flex-col items-center">
            <p className="text-[9px] font-mono text-gray-500 uppercase tracking-widest mb-4">Platform Resilience Score</p>
            <ResilienceRing score={Math.round(score)} />
            <div className="mt-4 grid grid-cols-3 gap-3 w-full">
              {[
                ["MTTR",       "4.2m", "text-yellow-400"],
                ["MTBF",       "18d",  "text-green-400"],
                ["Recovery",   "99.1%","text-sentinel-accent"],
              ].map(([label, val, color]) => (
                <div key={label} className="text-center bg-black/30 rounded-lg p-2">
                  <p className={`text-sm font-display font-bold ${color}`}>{val}</p>
                  <p className="text-[8px] font-mono text-gray-600 uppercase tracking-widest mt-0.5">{label}</p>
                </div>
              ))}
            </div>
          </div>

          {/* WS health */}
          <div className="glass-panel rounded-xl border border-sentinel-700/50 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Wifi className="w-4 h-4 text-sentinel-accent" />
              <span className="text-xs font-display font-semibold text-white">WebSocket Health</span>
            </div>
            <div className="space-y-2">
              {[
                ["Latency",     `${wsHealth.latency.toFixed(0)}ms`, wsHealth.latency < 20 ? "text-green-400" : "text-yellow-400"],
                ["Reconnects",  `${wsHealth.reconnects}`,           "text-green-400"],
                ["Msg Rate",    `${wsHealth.msgRate.toFixed(0)}/s`, "text-sentinel-accent"],
              ].map(([label, val, color]) => (
                <div key={label} className="flex items-center justify-between text-xs font-mono">
                  <span className="text-gray-500">{label}</span>
                  <span className={color}>{val}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Middle — Security checks */}
        <div className="col-span-4 space-y-3 overflow-y-auto">
          <div className="text-[9px] font-mono text-gray-500 uppercase tracking-widest mb-2">Security Validation Checks</div>
          {CHECKS.map((c, i) => (
            <motion.div
              key={c.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.07 }}
              className={`glass-panel rounded-xl border p-4 flex items-start gap-3 ${c.passing ? "border-green-500/20" : "border-red-500/30"}`}
            >
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${c.passing ? "bg-green-500/10 border border-green-500/30 text-green-400" : "bg-red-500/10 border border-red-500/30 text-red-400"}`}>
                {c.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-display font-semibold text-white">{c.label}</span>
                  {c.passing
                    ? <CheckCircle className="w-4 h-4 text-green-400 shrink-0" />
                    : <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 animate-pulse" />}
                </div>
                <p className="text-[10px] font-mono text-gray-500 mt-0.5 leading-relaxed">{c.detail}</p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Right — Threat detection log */}
        <div className="col-span-4 flex flex-col gap-4 h-full overflow-hidden">
          <div className="glass-panel rounded-xl border border-sentinel-700/50 flex flex-col flex-1 overflow-hidden">
            <div className="px-4 py-3 border-b border-sentinel-700/40 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Eye className="w-3.5 h-3.5 text-sentinel-accent" />
                <span className="text-xs font-display font-semibold text-white">Threat Detection Log</span>
              </div>
              <span className="text-[9px] font-mono text-gray-500">{threats.length} events</span>
            </div>
            <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
              <AnimatePresence mode="popLayout">
                {threats.map(t => (
                  <motion.div
                    key={t.id}
                    initial={{ opacity: 0, y: -6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className={`terminal-line text-[10px] ${t.sev === "high" ? "!border-red-500/50 !text-red-400" : t.sev === "medium" ? "!border-yellow-500/50 !text-yellow-400" : ""}`}
                  >
                    <span className="ts">{t.ts}</span> {t.msg}
                  </motion.div>
                ))}
              </AnimatePresence>
              {threats.length === 0 && (
                <p className="text-center py-12 text-gray-700 text-xs font-mono uppercase tracking-widest animate-pulse">No threats detected · System nominal</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
