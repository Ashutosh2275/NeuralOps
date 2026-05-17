import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "../lib/api";
import {
  Zap, Play, Film, RotateCcw, GitBranch, Shield, Terminal,
  AlertTriangle, CheckCircle, Radio, Clapperboard, Cpu
} from "lucide-react";

const SCENARIOS = [
  { id: "cascading_failure", label: "Cascading Failure",      icon: <GitBranch className="w-5 h-5" />, color: "text-red-400",    border: "border-red-500/40",    bg: "bg-red-500/10",    desc: "Memory leak → OOMKill → API cascade across 4 services" },
  { id: "api_meltdown",      label: "API Gateway Meltdown",   icon: <Zap className="w-5 h-5" />,       color: "text-orange-400", border: "border-orange-500/40", bg: "bg-orange-500/10", desc: "Traffic spike → connection pool exhaustion → gateway timeout" },
  { id: "database_failure",  label: "Database Blackout",      icon: <AlertTriangle className="w-5 h-5"/>,color:"text-yellow-400",border: "border-yellow-500/40", bg: "bg-yellow-500/10", desc: "PVC exhaustion → postgres OOM → dependent service failures" },
  { id: "network_partition", label: "Network Partition",      icon: <Radio className="w-5 h-5" />,      color: "text-blue-400",   border: "border-blue-500/40",   bg: "bg-blue-500/10",   desc: "Pod-to-pod latency spike → circuit breaker open → split-brain" },
  { id: "cpu_spike",         label: "CPU Resource Storm",     icon: <Cpu className="w-5 h-5" />,        color: "text-purple-400", border: "border-purple-500/40", bg: "bg-purple-500/10", desc: "Runaway compute → throttling → cascading dependency delays" },
];

interface ScenarioResult { incident_count: number; simulation_ids: string[]; status: string; }

const DEMO_STEPS = [
  { id: 1, label: "Dashboard", desc: "Show live KPI + topology overview" },
  { id: 2, label: "Trigger Failure", desc: "Inject cascading failure scenario" },
  { id: 3, label: "AI Triage", desc: "Watch multi-agent AI reasoning activate" },
  { id: 4, label: "Topology Map", desc: "See blast radius propagate across graph" },
  { id: 5, label: "Incident Detail", desc: "Drill into RCA + cascade chain" },
  { id: 6, label: "Cinematic Replay", desc: "Play movie-like incident reconstruction" },
];

export default function DemoCenter() {
  const [loading, setLoading] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, ScenarioResult>>({});
  const [log, setLog] = useState<string[]>([]);
  const [activeStep, setActiveStep] = useState(0);
  const [demoMode, setDemoMode] = useState(false);

  const trigger = async (scenario: string) => {
    setLoading(scenario);
    setLog(prev => [`[${new Date().toLocaleTimeString()}] Injecting scenario: ${scenario}...`, ...prev]);
    try {
      const res = await api.triggerScenario(scenario);
      setResults(prev => ({ ...prev, [scenario]: res }));
      setLog(prev => [
        `[${new Date().toLocaleTimeString()}] ✓ ${scenario}: ${res.incident_count} incidents created`,
        `[${new Date().toLocaleTimeString()}] IDs: ${res.simulation_ids.slice(0,2).join(", ")}`,
        ...prev,
      ]);
    } catch {
      setLog(prev => [`[${new Date().toLocaleTimeString()}] ✗ ${scenario}: trigger failed (backend may be seeding)`, ...prev]);
    }
    setLoading(null);
  };

  const runAutoDemoFlow = async () => {
    setDemoMode(true);
    setActiveStep(1);
    for (let i = 0; i < DEMO_STEPS.length; i++) {
      setActiveStep(i + 1);
      if (i === 1) await trigger("cascading_failure");
      await new Promise(r => setTimeout(r, 3000));
    }
    setActiveStep(0);
    setDemoMode(false);
  };

  return (
    <div className="h-full flex flex-col gap-6">
      <header className="flex items-end justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-yellow-500/10 border border-yellow-500/30 rounded-xl flex items-center justify-center shadow-[0_0_25px_rgba(234,179,8,0.2)]">
            <Clapperboard className="w-6 h-6 text-yellow-400" />
          </div>
          <div>
            <h1 className="page-title" style={{ textShadow: "0 0 20px rgba(234,179,8,0.4)" }}>Demo Control Center</h1>
            <p className="text-[10px] font-mono text-gray-500 uppercase tracking-widest mt-1">Chaos injection · Automated demo flows · Judge presentation</p>
          </div>
        </div>
        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          onClick={runAutoDemoFlow}
          disabled={demoMode}
          className="flex items-center gap-2 px-5 py-2.5 bg-yellow-500/20 border border-yellow-500/50 rounded-xl text-yellow-400 font-display font-semibold text-sm hover:bg-yellow-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ boxShadow: "0 0 20px rgba(234,179,8,0.2)" }}
        >
          <Play className="w-4 h-4" />
          {demoMode ? "Demo Running..." : "Auto Demo Flow"}
        </motion.button>
      </header>

      <div className="grid grid-cols-12 gap-6 flex-1 min-h-0">
        {/* Scenario cards */}
        <div className="col-span-7 space-y-4 overflow-y-auto pr-1">
          <div className="text-[9px] font-mono text-gray-500 uppercase tracking-widest mb-2">Chaos Scenarios — One-Click Injection</div>
          {SCENARIOS.map((s, i) => {
            const res = results[s.id];
            const isLoading = loading === s.id;
            return (
              <motion.div
                key={s.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.07 }}
                className={`glass-panel rounded-xl border ${s.border} p-5 group`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-4 flex-1">
                    <div className={`w-10 h-10 rounded-lg ${s.bg} border ${s.border} flex items-center justify-center ${s.color} shrink-0`}>
                      {s.icon}
                    </div>
                    <div className="flex-1">
                      <h3 className="text-sm font-display font-bold text-white">{s.label}</h3>
                      <p className="text-xs font-sans text-gray-400 mt-1 leading-relaxed">{s.desc}</p>
                      {res && (
                        <motion.div
                          initial={{ opacity: 0, y: 4 }}
                          animate={{ opacity: 1, y: 0 }}
                          className="mt-2 flex items-center gap-3 text-[9px] font-mono"
                        >
                          <span className="badge-low px-2 py-0.5 rounded text-[9px]">✓ {res.incident_count} incidents created</span>
                          <span className="text-gray-600">{res.simulation_ids.length} simulations</span>
                        </motion.div>
                      )}
                    </div>
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.96 }}
                    onClick={() => trigger(s.id)}
                    disabled={!!loading}
                    className={`shrink-0 px-4 py-2 rounded-lg border ${s.border} ${s.bg} ${s.color} text-xs font-mono uppercase tracking-widest hover:brightness-110 transition-all disabled:opacity-40 flex items-center gap-2`}
                  >
                    {isLoading ? <><div className="w-3 h-3 border-t border-current rounded-full animate-spin" /> Injecting</> : <><Zap className="w-3 h-3" /> Trigger</>}
                  </motion.button>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Right panel — demo flow + log */}
        <div className="col-span-5 flex flex-col gap-4 h-full overflow-hidden">
          {/* Demo flow stepper */}
          <div className="glass-panel rounded-xl border border-yellow-500/20 p-4">
            <div className="flex items-center gap-2 mb-4">
              <Film className="w-4 h-4 text-yellow-400" />
              <span className="text-xs font-display font-semibold text-white">Judge Demo Flow</span>
            </div>
            <div className="space-y-2">
              {DEMO_STEPS.map((step) => (
                <div key={step.id} className={`flex items-center gap-3 p-2.5 rounded-lg transition-all duration-500 ${activeStep === step.id ? "bg-yellow-500/15 border border-yellow-500/30" : activeStep > step.id ? "opacity-50" : ""}`}>
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-mono shrink-0 ${
                    activeStep > step.id ? "bg-sentinel-success text-white" :
                    activeStep === step.id ? "bg-yellow-500 text-black animate-pulse" :
                    "bg-sentinel-800 border border-sentinel-700/50 text-gray-500"
                  }`}>
                    {activeStep > step.id ? <CheckCircle className="w-3 h-3" /> : step.id}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-xs font-display font-semibold ${activeStep === step.id ? "text-yellow-400" : "text-gray-400"}`}>{step.label}</p>
                    <p className="text-[9px] font-mono text-gray-600 truncate">{step.desc}</p>
                  </div>
                  {activeStep === step.id && <div className="w-3 h-3 border-t-2 border-yellow-500 rounded-full animate-spin shrink-0" />}
                </div>
              ))}
            </div>
          </div>

          {/* Live log */}
          <div className="glass-panel rounded-xl border border-sentinel-700/50 flex flex-col flex-1 overflow-hidden">
            <div className="px-4 py-3 border-b border-sentinel-700/40 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Terminal className="w-3.5 h-3.5 text-sentinel-accent" />
                <span className="text-xs font-display font-semibold text-white">Injection Log</span>
              </div>
              <button onClick={() => setLog([])} className="text-[9px] font-mono text-gray-600 hover:text-gray-400 uppercase tracking-widest">Clear</button>
            </div>
            <div className="flex-1 overflow-y-auto p-3 space-y-1">
              <AnimatePresence mode="popLayout">
                {log.map((line, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: -6 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`terminal-line text-[10px] ${line.includes("✓") ? "!border-green-500/50 !text-green-400" : line.includes("✗") ? "!border-red-500/50 !text-red-400" : ""}`}
                  >
                    {line}
                  </motion.div>
                ))}
              </AnimatePresence>
              {log.length === 0 && (
                <p className="text-center text-gray-700 text-xs font-mono uppercase tracking-widest py-8 animate-pulse">Ready to inject chaos...</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
