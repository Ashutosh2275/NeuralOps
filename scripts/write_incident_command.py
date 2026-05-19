import os

file_path = "frontend/src/pages/IncidentCommandCenter.tsx"

content = """import React, { useEffect, useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { usePlatform, useReasoningLog } from "../contexts/PlatformContext";
import {
  Activity, AlertTriangle, Shield, Terminal, Clock, Server, CheckCircle, 
  Cpu, Zap, TrendingUp, ChevronRight, CornerDownRight, Crosshair, Network
} from "lucide-react";
import DependencyGraph from "../components/topology/DependencyGraph";

// ── Shared UI Settings ───────────────────────────────────────────────────
const P = {
  background: "rgba(10, 16, 28, 0.75)",
  backdropFilter: "blur(12px)",
  border: "1px solid rgba(40, 65, 105, 0.3)",
  borderRadius: 12,
  boxShadow: "0 8px 32px rgba(0, 0, 0, 0.4)"
};

const PH = {
  fontSize: "0.55rem",
  fontFamily: "Space Grotesk",
  letterSpacing: "0.15em",
  textTransform: "uppercase" as const,
  color: "rgba(255, 255, 255, 0.45)",
  marginBottom: 10,
  display: "flex",
  alignItems: "center",
  gap: 6
};

// ── Fallback Data Generation ─────────────────────────────────────────────
const FALLBACK_SERVICES = [
  { id: "api-gateway", name: "API Gateway", status: "degraded", cpu: 89, lat: "1.4s" },
  { id: "auth-service", name: "Auth Svc", status: "healthy", cpu: 42, lat: "45ms" },
  { id: "payment-queue", name: "Payment Queue", status: "critical", cpu: 99, lat: "TIMEOUT" },
  { id: "postgres-main", name: "Postgres DB", status: "degraded", cpu: 75, lat: "800ms" },
  { id: "inventory-cache", name: "Redis Cache", status: "healthy", cpu: 22, lat: "12ms" },
];

const FALLBACK_REMEDIATION = [
  { id: "R-1", text: "Isolating anomalous traffic on Payment Queue", status: "completed" },
  { id: "R-2", text: "Draining stalled connections on Postgres DB", status: "completed" },
  { id: "R-3", text: "Scaling API Gateway replicas (3 → 6)", status: "active" },
  { id: "R-4", text: "Validating SLA latency recovery", status: "pending" },
  { id: "R-5", text: "Resolving incident INC-2049", status: "pending" },
];

// ── Sub-Components ───────────────────────────────────────────────────────
function CognitiveStream() {
  const reasoning = useReasoningLog();
  
  // Use real reasoning, fallback if empty
  const defaultReasoning = [
    { id: '1', kind: 'critical', agent: 'RCACore', text: 'Cascading latency detected originating from payment-queue.' },
    { id: '2', kind: 'info', agent: 'Predictive', text: 'Analyzing blast radius: Postgres DB at 74% risk.' },
    { id: '3', kind: 'warn', agent: 'Correlator', text: 'TCP timeouts correlating with high Memory IO.' }
  ];
  const items = reasoning?.length > 0 ? reasoning : defaultReasoning;

  return (
    <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 8, padding: "0 4px" }}>
      <AnimatePresence mode="popLayout">
        {items.slice(0, 15).map((log: any) => {
          const c = log.kind === "critical" ? "#ef4444" : log.kind === "warn" ? "#f97316" : log.kind === "success" ? "#10b981" : "#22d3ee";
          return (
             <motion.div key={log.id} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }}
               style={{
                 background: `linear-gradient(90deg, ${c}11, transparent)`,
                 borderLeft: `2px solid ${c}`, padding: "0.5rem 0.75rem", borderRadius: "0 6px 6px 0",
                 fontFamily: "JetBrains Mono", fontSize: "0.55rem", lineHeight: 1.5, color: "rgba(255,255,255,0.75)"
               }}>
               <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                 <span style={{ color: c, fontWeight: 700 }}>[{log.agent}]</span>
                 <span style={{ color: "rgba(255,255,255,0.3)" }}>{log.ts || new Date().toLocaleTimeString()}</span>
               </div>
               <div>{log.text}</div>
             </motion.div>
          )
        })}
      </AnimatePresence>
    </div>
  );
}

function ServiceImpactMatrix( { topology }: { topology: any } ) {
  const [svcs, setSvcs] = useState(FALLBACK_SERVICES);
  
  // Mock live fluctuations
  useEffect(() => {
    const t = setInterval(() => {
      setSvcs(prev => prev.map(s => ({
        ...s,
        cpu: s.status === 'critical' ? Math.min(100, s.cpu + Math.floor(Math.random() * 5)) : Math.max(10, Math.min(95, s.cpu + Math.floor((Math.random() - 0.5) * 6)))
      })));
    }, 2000);
    return () => clearInterval(t);
  }, []);

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 6, overflowY: "auto" }}>
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr", gap: 8, padding: "0 10px 6px",
        borderBottom: "1px solid rgba(255,255,255,0.1)", fontSize: "0.5rem", fontFamily: "Space Grotesk", color: "rgba(255,255,255,0.4)" }}>
        <span>SERVICE</span><span>LATENCY</span><span>CPU / STATUS</span>
      </div>
      {svcs.map(s => {
        const c = s.status === 'healthy' ? '#10b981' : s.status === 'critical' ? '#ef4444' : '#f97316';
        return (
          <div key={s.id} style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr", gap: 8, alignItems: "center",
            padding: "0.4rem 0.6rem", background: "rgba(255,255,255,0.02)", borderRadius: 6 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <div style={{ width: 6, height: 6, borderRadius: "50%", background: c, boxShadow: `0 0 8px ${c}` }} />
              <span style={{ fontSize: "0.55rem", fontFamily: "JetBrains Mono", color: "rgba(255,255,255,0.8)" }}>{s.name}</span>
            </div>
            <span style={{ fontSize: "0.55rem", fontFamily: "JetBrains Mono", color: c }}>{s.lat}</span>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
               <div style={{ flex: 1, height: 2, background: "rgba(255,255,255,0.1)", borderRadius: 2 }}>
                 <motion.div animate={{ width: `${s.cpu}%` }} transition={{ duration: 0.5 }} style={{ height: "100%", background: c, borderRadius: 2 }} />
               </div>
               <span style={{ fontSize: "0.5rem", fontFamily: "JetBrains Mono", color: c, width: 22, textAlign: "right" }}>{s.cpu}%</span>
            </div>
          </div>
        )
      })}
    </div>
  );
}

function RemediationTimeline() {
  const [steps, setSteps] = useState(FALLBACK_REMEDIATION);
  const [progress, setProgress] = useState(40);

  useEffect(() => {
    const t = setInterval(() => {
      setProgress(p => {
        if (p >= 80) return p;
        if (p === 60) {
          setSteps(s => s.map(st => st.id === "R-3" ? { ...st, status: "completed" } : st.id === "R-4" ? { ...st, status: "active" } : st));
        }
        return p + 20;
      });
    }, 4500);
    return () => clearInterval(t);
  }, []);

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 12, overflow: "hidden" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: "0.55rem", fontFamily: "JetBrains Mono", color: "rgba(255,255,255,0.5)" }}>WORKFLOW: INC-MITIGATION-Alpha</span>
        <span style={{ fontSize: "0.55rem", fontFamily: "JetBrains Mono", color: "#22d3ee" }}>{progress}% COMPLETE</span>
      </div>
      <div style={{ height: 2, background: "rgba(255,255,255,0.08)", borderRadius: 2, overflow: "hidden" }}>
        <motion.div animate={{ width: `${progress}%` }} style={{ height: "100%", background: "linear-gradient(90deg, #3b82f6, #22d3ee)", borderRadius: 2 }} />
      </div>
      <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 8, padding: "8px 4px" }}>
        {steps.map((st, i) => (
          <div key={st.id} style={{ display: "flex", gap: 10, opacity: st.status === 'pending' ? 0.3 : 1 }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 2 }}>
              <div style={{ 
                width: 14, height: 14, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
                background: st.status === 'completed' ? "#10b981" : st.status === 'active' ? "rgba(34,211,238,0.2)" : "transparent",
                border: `1px solid ${st.status === 'completed' ? "#10b981" : st.status === 'active' ? "#22d3ee" : "rgba(255,255,255,0.2)"}`,
                animation: st.status === 'active' ? "pulse-cyan 2s infinite" : "none"
              }}>
                {st.status === 'completed' && <CheckCircle style={{ width: 8, height: 8, color: "white" }} />}
                {st.status === 'active' && <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#22d3ee" }} />}
              </div>
              {i < steps.length -1 && <div style={{ width: 1, flex: 1, background: st.status === 'completed' ? "#10b981" : "rgba(255,255,255,0.1)", minHeight: 12 }} />}
            </div>
            <div style={{ fontSize: "0.55rem", fontFamily: "JetBrains Mono", lineHeight: 1.4, color: st.status === 'completed' ? "rgba(255,255,255,0.5)" : st.status === 'active' ? "#22d3ee" : "rgba(255,255,255,0.3)", paddingBottom: 12 }}>
              {st.text}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function ConsensusForecast() {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16, alignItems: "center", height: "100%" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <span style={{ fontSize: "0.5rem", fontFamily: "Space Grotesk", color: "rgba(255,255,255,0.4)" }}>PREDICTED STABILIZATION</span>
        <span style={{ fontSize: "1.2rem", fontFamily: "Space Grotesk", fontWeight: 700, color: "#10b981" }}>1m 45s</span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 4, paddingLeft: 16, borderLeft: "1px solid rgba(255,255,255,0.1)" }}>
        <span style={{ fontSize: "0.5rem", fontFamily: "Space Grotesk", color: "rgba(255,255,255,0.4)" }}>AI CONFIDENCE SCORE</span>
        <span style={{ fontSize: "1.2rem", fontFamily: "Space Grotesk", fontWeight: 700, color: "#22d3ee" }}>94.2%</span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 4, paddingLeft: 16, borderLeft: "1px solid rgba(255,255,255,0.1)" }}>
        <span style={{ fontSize: "0.5rem", fontFamily: "Space Grotesk", color: "rgba(255,255,255,0.4)" }}>RECOMMENDED PATH</span>
        <span style={{ fontSize: "0.6rem", fontFamily: "JetBrains Mono", color: "#f97316" }}>Isolate Payment Queue</span>
      </div>
    </div>
  )
}

// ── Main Page ────────────────────────────────────────────────────────────
export default function IncidentCommandCenter() {
  const { state } = usePlatform();
  const { topology, criticalCount, incidents } = state;
  const activeIncident = incidents[0] || { title: "INC-2049: Latency Cascade", severity: "critical", id: "INC-2049" };

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", gap: 16, minHeight: 0, paddingRight: 4 }}>
      
      {/* ── Top Command Bar ────────────────────────────────────────────── */}
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ width: 44, height: 44, background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.4)", borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 0 20px rgba(239, 68, 68, 0.2)" }}>
            <AlertTriangle style={{ width: 22, height: 22, color: "#ef4444" }} className="animate-pulse" />
          </div>
          <div>
            <h1 style={{ fontSize: "1.5rem", fontWeight: 800, fontFamily: "Space Grotesk", color: "#ef4444", textShadow: "0 0 16px rgba(239, 68, 68, 0.5)", margin: 0, lineHeight: 1.1 }}>
              ACTIVE INCIDENT COMMAND
            </h1>
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 4 }}>
              <span style={{ fontSize: "0.55rem", fontFamily: "JetBrains Mono", color: "rgba(255,255,255,0.5)", textTransform: "uppercase" }}>Targeting:</span>
              <span style={{ fontSize: "0.55rem", fontFamily: "Space Grotesk", fontWeight: 700, color: "#fff", background: "rgba(255,255,255,0.1)", padding: "2px 6px", borderRadius: 4 }}>
                {activeIncident.title}
              </span>
            </div>
          </div>
        </div>

        <div style={{ display: "flex", gap: 12 }}>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 2 }}>
            <span style={{ fontSize: "0.5rem", fontFamily: "JetBrains Mono", color: "rgba(255,255,255,0.4)", textTransform: "uppercase" }}>SLA Degradation</span>
            <span style={{ fontSize: "1.1rem", fontFamily: "Space Grotesk", fontWeight: 700, color: "#f97316" }}>-0.42%</span>
          </div>
          <div style={{ width: 1, background: "rgba(255,255,255,0.1)", margin: "0 4px" }} />
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 2 }}>
            <span style={{ fontSize: "0.5rem", fontFamily: "JetBrains Mono", color: "rgba(255,255,255,0.4)", textTransform: "uppercase" }}>Critical Nodes Affected</span>
            <span style={{ fontSize: "1.1rem", fontFamily: "Space Grotesk", fontWeight: 700, color: "#ef4444" }}>{criticalCount || 2}</span>
          </div>
          <div style={{ width: 1, background: "rgba(255,255,255,0.1)", margin: "0 4px" }} />
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 2 }}>
             <span style={{ fontSize: "0.5rem", fontFamily: "JetBrains Mono", color: "rgba(255,255,255,0.4)", textTransform: "uppercase" }}>Active Agents</span>
             <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
               <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#22d3ee", boxShadow: "0 0 8px #22d3ee" }} />
               <span style={{ fontSize: "1.1rem", fontFamily: "Space Grotesk", fontWeight: 700, color: "#22d3ee" }}>3</span>
             </div>
          </div>
        </div>
      </header>

      {/* ── Main Operations Grid ───────────────────────────────────────── */}
      <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1.1fr 1.3fr 1fr", gap: 16, minHeight: 0 }}>
        
        {/* LEFT PANEL: Cognitive Stream & Mini Map */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16, minHeight: 0 }}>
          <div style={{ ...P, flex: 1, display: "flex", flexDirection: "column", padding: "1rem", overflow: "hidden" }}>
            <div style={PH}><Cpu size={14} color="#22d3ee" /> Cognitive Engine Stream</div>
            <CognitiveStream />
          </div>
          <div style={{ ...P, height: 180, display: "flex", flexDirection: "column", padding: "0.8rem", overflow: "hidden", flexShrink: 0 }}>
            <div style={PH}><Network size={14} color="#f97316" /> Blast Radius / Mini Topology</div>
            <div style={{ flex: 1, position: "relative", borderRadius: 8, overflow: "hidden", border: "1px solid rgba(255,255,255,0.05)", background: "rgba(0,0,0,0.2)" }}>
              {topology ? <DependencyGraph graph={topology} width={300} height={150} /> : <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", fontSize: "0.5rem", fontFamily: "JetBrains Mono", color: "rgba(255,255,255,0.2)" }}>NO TOPOLOGY SIGNAL</div>}
            </div>
          </div>
        </div>

        {/* CENTER PANEL: Incident Remediation Timeline */}
        <div style={{ ...P, display: "flex", flexDirection: "column", padding: "1rem", minHeight: 0 }}>
          <div style={PH}><Terminal size={14} color="#10b981" /> Remediation Orchestration</div>
          <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 16, marginTop: 8, overflow: "hidden" }}>
             <RemediationTimeline />
             
             {/* Sub-panel in center for live action log */}
             <div style={{ height: 120, background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.05)", borderRadius: 8, padding: "0.5rem", overflowY: "auto", fontFamily: "JetBrains Mono", fontSize: "0.5rem", color: "rgba(255,255,255,0.4)" }}>
               <div style={{ color: "#22d3ee", marginBottom: 4 }}>$ neural-agent orchestrate --incident INC-2049</div>
               <div>[SUCCESS] Lock acquired on api-gateway-0</div>
               <div>[INFO] Draining 1402 active sessions...</div>
               <div>[SUCCESS] Postgres connection pool flushed.</div>
               <div style={{ color: "#10b981" }}>[ACTIVE] Awaiting replica health validation (6/6 pending)</div>
             </div>
          </div>
        </div>

        {/* RIGHT PANEL: Service Impact Matrix */}
        <div style={{ ...P, display: "flex", flexDirection: "column", padding: "1rem", minHeight: 0 }}>
          <div style={PH}><Server size={14} color="#f97316" /> Service Impact Matrix</div>
          <ServiceImpactMatrix topology={topology} />
        </div>
      </div>

      {/* ── Bottom Section: AI Consensus & Forecast ────────────────────── */}
      <div style={{ ...P, height: 90, padding: "1rem 1.5rem", display: "flex", flexShrink: 0 }}>
        <div style={{ flex: 1 }}>
           <div style={PH}><Crosshair size={14} color="#eab308" /> AI Consensus & Recovery Forecast</div>
           <ConsensusForecast />
        </div>
      </div>

    </div>
  );
}
"""

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("IncidentCommandCenter rewritten with Enterprise aesthetics!")