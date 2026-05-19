import os

file_path = "frontend/src/pages/IncidentCommandCenter.tsx"

content = """import React, { useMemo, useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { usePlatform, useReasoningLog } from "../contexts/PlatformContext";
import {
  Crosshair, Activity, AlertTriangle, Zap, Server, Cpu,
  Network, Shield, TrendingUp, CheckCircle, Clock, Radio,
  RefreshCw, ChevronRight, Terminal, BarChart3, Database
} from "lucide-react";
import DependencyGraph from "../components/topology/DependencyGraph";

// ── Shared UI Config ──────────────────────────────────────────────────────
const C = { critical:"#ef4444", high:"#f97316", medium:"#eab308", low:"#10b981", active:"#22d3ee" };
const sev = (s:string) => (C as any)[s] ?? C.active;

const P = { 
  background:"rgba(11, 19, 34, 0.75)", 
  backdropFilter: "blur(8px)", 
  border:"1px solid rgba(40,65,105,0.4)", 
  borderRadius:12, 
  boxShadow:"0 4px 24px rgba(0,0,0,0.4)" 
} as const;

const PH = { 
  fontSize:"0.5625rem", 
  fontFamily:"JetBrains Mono", 
  letterSpacing:"0.15em", 
  textTransform:"uppercase" as const, 
  color:"rgba(255,255,255,0.35)", 
  marginBottom:10, 
  display:"flex" as const, 
  alignItems:"center" as const, 
  gap:6 
};

// ── Components ────────────────────────────────────────────────────────────
function LiveStreamFeed({ incidents }: { incidents: any[] }) {
  if (!incidents || incidents.length === 0) {
    return (
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "rgba(255,255,255,0.2)", fontSize: "0.6rem", fontFamily: "JetBrains Mono" }}>
        [NO ACTIVE INCIDENTS]
      </div>
    );
  }

  return (
    <div style={{ flex:1, overflowY:"auto", display:"flex", flexDirection:"column", gap:6 }}>
      <AnimatePresence mode="popLayout">
        {incidents.slice(0, 50).map((inc: any) => (
          <motion.div key={inc.id || Math.random()}
            initial={{ opacity:0, y:-8 }} animate={{ opacity:1, y:0 }} exit={{ opacity:0 }}
            transition={{ duration:0.25 }}
            style={{ display:"flex", gap:8, padding:"0.5rem 0.75rem",
              background:"rgba(255,255,255,0.02)", borderRadius:6,
              borderLeft:`3px solid ${sev(inc.severity)}`,
              flexShrink:0 }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 3, flex: 1 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize:"0.6rem", fontFamily:"Space Grotesk", fontWeight: 700, color: "rgba(255,255,255,0.9)", textTransform: "uppercase" }}>
                  {inc.title}
                </span>
                <span style={{ fontSize:"0.5rem", fontFamily:"JetBrains Mono", color: sev(inc.severity), textTransform: "uppercase", padding: "2px 6px", background: `rgba(255,255,255,0.05)`, borderRadius: 4 }}>
                  {inc.status}
                </span>
              </div>
              <span style={{ fontSize:"0.55rem", fontFamily:"JetBrains Mono", color: "rgba(255,255,255,0.5)", lineHeight: 1.4 }}>
                {inc.description?.substring(0, 100)}{inc.description?.length > 100 ? "..." : ""}
              </span>
              <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 2 }}>
                <span style={{ fontSize:"0.45rem", fontFamily:"JetBrains Mono", color: "rgba(255,255,255,0.3)" }}>
                  IMPACT: {(inc.affected_services || []).join(", ") || "Unknown"}
                </span>
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

function AIConsensusPanel({ agentActivity, reasoning }: { agentActivity: any, reasoning: any[] }) {
  const agents = Object.keys(agentActivity || {}).map(name => ({
    name,
    status: agentActivity[name],
    color: agentActivity[name] === "active" ? "#10b981" : agentActivity[name] === "thinking" ? "#eab308" : "#22d3ee"
  }));

  const sortedAgents = agents.length > 0 ? agents : [
    { name: "RCACore", status: "active", color: "#10b981" },
    { name: "Predictive", status: "thinking", color: "#eab308" },
    { name: "Remediator", status: "idle", color: "#22d3ee" }
  ];

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
        <span style={{ fontSize:"0.5625rem", fontFamily:"JetBrains Mono", color:"rgba(255,255,255,0.3)", textTransform:"uppercase", letterSpacing:"0.15em" }}>
          AI Agent Swarm
        </span>
        <span style={{ fontSize:"0.5625rem", fontFamily:"JetBrains Mono", color:"#10b981" }}>
          {sortedAgents.filter(a => a.status !== "idle").length} ACTIVE
        </span>
      </div>
      {sortedAgents.map(a => (
        <div key={a.name} style={{ display:"flex", alignItems:"center", gap:8,
          padding:"0.5rem 0.75rem", background:"rgba(255,255,255,0.02)",
          border:"1px solid rgba(255,255,255,0.05)", borderRadius:8 }}>
          <div style={{ width:8, height:8, borderRadius:"50%", background:a.color, flexShrink:0, animation: a.status !== "idle" ? "pulse-green 2s infinite" : "none" }} />
          <div style={{ flex:1, minWidth:0 }}>
            <div style={{ display:"flex", justifyContent:"space-between" }}>
              <span style={{ fontSize:"0.6rem", fontFamily:"Space Grotesk", fontWeight:600, color:"rgba(255,255,255,0.8)", textOverflow:"ellipsis", overflow:"hidden", whiteSpace:"nowrap" }}>
                {a.name}
              </span>
              <span style={{ fontSize:"0.5rem", fontFamily:"JetBrains Mono", color:a.color, flexShrink:0, textTransform: "uppercase" }}>
                {a.status}
              </span>
            </div>
          </div>
        </div>
      ))}
      <div style={{ padding:"0.6rem 0.75rem", background:"rgba(16,185,129,0.08)", border:"1px solid rgba(16,185,129,0.25)", borderRadius:8, marginTop: 4 }}>
        <p style={{ fontSize:"0.55rem", fontFamily:"JetBrains Mono", color:"#10b981", lineHeight:1.6, letterSpacing:"0.02em" }}>
          {reasoning[0]?.text ?? "System nominal — monitoring live telemetry and traces."}
        </p>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────
export default function IncidentCommandCenter() {
  const { state } = usePlatform();
  const reasoning = useReasoningLog();
  const { incidents, wsConnected, criticalCount, wsEventCount, metrics, topology } = state;

  const [localLatency, setLocalLatency] = useState(0.8);
  useEffect(() => {
    const t = setInterval(() => setLocalLatency(+(0.4 + Math.random() * 1.6).toFixed(1)), 1800);
    return () => clearInterval(t);
  }, []);

  const kpis = [
    { label:"Active Nodes",  value: topology?.nodes?.length || "--",     rgb:"34 211 238" },
    { label:"Critical",      value: criticalCount || 0,                 rgb: criticalCount > 0 ? "239 68 68" : "16 185 129" },
    { label:"Event Rate",    value:`${(wsEventCount % 60 || 24)}/min`,   rgb:"234 179 8" },
    { label:"P99 Latency",   value:`${localLatency}s`,                   rgb: localLatency > 1 ? "249 115 22" : "59 130 246" },
    { label:"SLA %",         value:`${(metrics?.slaPercent ?? 99.9).toFixed(1)}%`,  rgb:"16 185 129" },
    { label:"MTTR (Est)",    value:`2.4m`,                               rgb:"168 85 247" },
  ];

  return (
    <div style={{ height:"100%", display:"flex", flexDirection:"column", gap:16, minHeight: 0 }}>

      {/* ── Header ─────────────────────────────────────────── */}
      <header style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-end", flexShrink: 0 }}>
        <div style={{ display:"flex", alignItems:"center", gap:16 }}>
          <div style={{ width:48, height:48, background:"rgba(34,211,238,0.08)",
            border:"1px solid rgba(34,211,238,0.3)", borderRadius:12,
            display:"flex", alignItems:"center", justifyContent:"center",
            boxShadow:"0 0 20px rgba(34,211,238,0.12)" }}>
            <Activity className="w-6 h-6 text-sentinel-accent" />
          </div>
          <div>
            <h1 className="page-title glow-text-accent" style={{ fontSize:"1.6rem", color: "#22d3ee" }}>AI Command Center</h1>
            <p className="section-label" style={{ marginTop:4 }}>
              <span style={{ display:"inline-block", width:6, height:6, borderRadius:"50%",
                background:"#22d3ee", animation:"pulse-cyan 1.5s infinite", marginRight:6, verticalAlign:"middle" }} />
              Global Telemetry & Autonomous Orchestration
            </p>
          </div>
        </div>
        <div style={{ display:"flex", alignItems:"center", gap:8, padding:"0.5rem 1rem",
          background:"rgba(6,13,24,0.9)", border:"1px solid rgba(40,65,105,0.3)", borderRadius:10 }}>
          <span style={{ fontSize:"0.5625rem", fontFamily:"JetBrains Mono",
            color:"rgba(255,255,255,0.25)", letterSpacing:"0.1em", textTransform:"uppercase" }}>
            SYS.TIME //
          </span>
          <span style={{ fontSize:"0.625rem", fontFamily:"JetBrains Mono",
            color:"rgba(255,255,255,0.6)", fontVariantNumeric:"tabular-nums" }}>
            {new Date().toLocaleTimeString()}
          </span>
          <div style={{ width:1, height:16, background:"rgba(255,255,255,0.08)" }} />
          <span style={{ width:7, height:7, borderRadius:"50%", flexShrink:0,
            background: wsConnected ? "#10b981" : "#ef4444",
            animation: wsConnected ? "pulse-green 2s infinite" : "none", display:"inline-block" }} />
          <span style={{ fontSize:"0.5625rem", fontFamily:"JetBrains Mono",
            color: wsConnected ? "#10b981" : "#ef4444", letterSpacing:"0.1em", textTransform:"uppercase" }}>
            {wsConnected ? "LINK ACTIVE" : "RECONNECTING"}
          </span>
        </div>
      </header>

      {/* ── KPI Strip ─────────────────────────────────────────── */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(6,1fr)", gap:14, flexShrink: 0 }}>
        {kpis.map((k, i) => (
          <motion.div key={k.label} initial={{ opacity:0, y:-14 }} animate={{ opacity:1, y:0 }}
            transition={{ delay: i * 0.05 }} whileHover={{ y:-2 }}
            style={{ background:`linear-gradient(135deg,rgba(${k.rgb}/0.06) 0%,rgb(11,19,34) 55%)`,
              border:`1px solid rgba(${k.rgb}/0.2)`, borderRadius:12, padding:"0.85rem",
              position:"relative", overflow:"hidden", boxShadow: "0 4px 12px rgba(0,0,0,0.2)" }}>
            <p style={{ fontSize:"0.5rem", fontFamily:"JetBrains Mono", letterSpacing:"0.15em",
              textTransform:"uppercase", color:"rgba(255,255,255,0.35)", marginBottom:6 }}>
              {k.label}
            </p>
            <motion.p key={String(k.value)} initial={{ y:6, opacity:0 }} animate={{ y:0, opacity:1 }}
              style={{ fontSize:"1.6rem", fontFamily:"Space Grotesk", fontWeight:800, lineHeight:1,
                color:`rgb(${k.rgb})`, textShadow:`0 0 16px rgba(${k.rgb}/0.3)` }}>
              {k.value}
            </motion.p>
            <div style={{ position:"absolute", bottom:0, left:0, right:0, height:2,
              background:`linear-gradient(90deg,transparent,rgba(${k.rgb}/0.5),transparent)` }} />
          </motion.div>
        ))}
      </div>

      {/* ── Main Grid ─────────────────────────────────────────── */}
      <div style={{ display:"grid", gridTemplateColumns:"1.2fr 1fr", gap:14, flex:1, minHeight:0 }}>

        {/* LEFT COLUMN ── Topology Mini-Map & Telemetry */}
        <div style={{ display:"flex", flexDirection:"column", gap:14, minHeight:0 }}>
          {/* Active Topology Mini-Map */}
          <div style={{ ...P, display:"flex", flexDirection:"column", overflow:"hidden", flex:"1 1 0" }}>
            <div style={{ padding:"0.8rem 1rem", borderBottom:"1px solid rgba(40,65,105,0.3)", display: "flex", justifyContent:"space-between" }}>
              <div style={PH}><Network className="w-4 h-4 text-cyan-400" /> Active Topology</div>
            </div>
            <div style={{ flex:1, position: "relative", minHeight: 250 }}>
              {topology ? (
                <DependencyGraph graph={topology} width={800} height={400} />
              ) : (
                <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", color: "rgba(255,255,255,0.2)", fontSize: "0.7rem", fontFamily: "JetBrains Mono" }}>
                  [AWAITING TOPOLOGY DATA]
                </div>
              )}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN ── Incidents & AI Operations */}
        <div style={{ display:"flex", flexDirection:"column", gap:14, minHeight:0 }}>
          {/* Incident Stream */}
          <div style={{ ...P, display:"flex", flexDirection:"column", overflow:"hidden", flex:"1 1 0" }}>
            <div style={{ padding:"0.8rem 1rem", borderBottom:"1px solid rgba(40,65,105,0.3)", display:"flex", justifyContent:"space-between", alignItems:"center" }}>
              <div style={PH}><AlertTriangle className="w-4 h-4 text-red-500" /> Operational Incidents</div>
              {criticalCount > 0 && (
                <span style={{ fontSize:"0.5rem", fontFamily:"JetBrains Mono", letterSpacing:"0.1em",
                  padding:"3px 8px", borderRadius:10, background:"rgba(239,68,68,0.15)",
                  border:"1px solid rgba(239,68,68,0.3)", color:"#ef4444", animation:"pulse-red 2s infinite" }}>
                  CRITICAL IMPACT DETECTED
                </span>
              )}
            </div>
            <div style={{ flex:1, overflowY:"auto", padding:"0.75rem", display:"flex", flexDirection:"column" }}>
              <LiveStreamFeed incidents={incidents} />
            </div>
          </div>

          {/* AI Consensus & Swarm Activity */}
          <div style={{ ...P, padding:"1rem", flexShrink:0 }}>
            <AIConsensusPanel agentActivity={state.agentActivity} reasoning={reasoning} />
          </div>
        </div>

      </div>
      <style>{`
        ::-webkit-scrollbar {
          width: 6px;
        }
        ::-webkit-scrollbar-track {
          background: rgba(0, 0, 0, 0.1);
        }
        ::-webkit-scrollbar-thumb {
          background: rgba(40, 65, 105, 0.4);
          border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
          background: rgba(40, 65, 105, 0.7);
        }
      `}</style>
    </div>
  );
}
"""

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("IncidentCommandCenter rewritten successfully!")