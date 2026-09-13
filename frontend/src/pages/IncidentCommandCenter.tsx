import React, { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import { usePlatform, useReasoningLog, type ReasoningEntry } from "../contexts/PlatformContext";
import {
  Activity, AlertTriangle, Shield, Terminal, Clock, Server, CheckCircle, 
  Cpu, Zap, TrendingUp, ChevronRight, CornerDownRight, Crosshair, Network
} from "lucide-react";
import DependencyGraph from "../components/topology/DependencyGraph";

// â”€â”€ Shared UI Settings â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

// â”€â”€ Fallback Data Generation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const FALLBACK_SERVICES = [
  { id: "api-gateway", name: "API Gateway", status: "degraded", cpu: 89, lat: "1.4s" },
  { id: "auth-service", name: "Auth Svc", status: "healthy", cpu: 42, lat: "45ms" },
  { id: "payment-queue", name: "Payment Queue", status: "critical", cpu: 99, lat: "TIMEOUT" },
  { id: "postgres-main", name: "Postgres DB", status: "degraded", cpu: 75, lat: "800ms" },
  { id: "inventory-cache", name: "Redis Cache", status: "healthy", cpu: 22, lat: "12ms" },
];

const FALLBACK_REMEDIATION = [
  { id: "R-1", phase: "ISOLATION", text: "Isolate anomalous traffic on Payment Queue", status: "completed", time: "0.8s" },
  { id: "R-2", phase: "MITIGATION", text: "Drain stalled connections on Postgres DB", status: "completed", time: "1.2s" },
  { id: "R-3", phase: "RECOVERY", text: "Scale API Gateway replicas (3 -> 6)", status: "active", time: "in-progress" },
  { id: "R-4", phase: "VALIDATION", text: "Healthcheck SLA latency bounds", status: "pending", time: "-" },
  { id: "R-5", phase: "RESOLUTION", text: "Close incident INC-2049", status: "pending", time: "-" },
];

const WAR_ROOM_SEED_LOGS: ReasoningEntry[] = [
  { id: "wr-seed-1", kind: "success", agent: "Summarizer", text: "SLA compliance: 99.1%. Within tolerance window.", ts: new Date().toLocaleTimeString() },
  { id: "wr-seed-2", kind: "warn", agent: "Network Monitor", text: "Network partition isolated to zone-b. No cross-zone propagation.", ts: new Date().toLocaleTimeString() },
  { id: "wr-seed-3", kind: "critical", agent: "Memory Agent", text: "Memory spike in catalog-service. RSS 1.8GB exceeds threshold.", ts: new Date().toLocaleTimeString() },
];

/** Append-only stream — never resets list; scroll inside fixed panel */
function CognitiveStream() {
  const reasoning = useReasoningLog();
  const scrollRef = useRef<HTMLDivElement>(null);
  const seenIdsRef = useRef<Set<string>>(new Set());
  const [stream, setStream] = useState<ReasoningEntry[]>(WAR_ROOM_SEED_LOGS);

  useEffect(() => {
    const fresh = reasoning.filter((e) => !seenIdsRef.current.has(e.id));
    if (fresh.length === 0) return;
    fresh.forEach((e) => seenIdsRef.current.add(e.id));
    const ordered = [...fresh].reverse();
    setStream((prev) => {
      const merged = [...prev, ...ordered];
      return merged.length > 200 ? merged.slice(-200) : merged;
    });
  }, [reasoning]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [stream.length]);

  return (
    <div
      ref={scrollRef}
      className="scrollbar-thin scrollbar-thumb-cyan-500/20 scrollbar-track-transparent"
      style={{
        flex: 1,
        minHeight: 0,
        overflowY: "auto",
        overflowX: "hidden",
        display: "flex",
        flexDirection: "column",
        gap: 8,
        padding: "0 8px 4px 4px",
      }}
    >
      {stream.map((log) => {
        const c =
          log.kind === "critical"
            ? "#ef4444"
            : log.kind === "warn"
              ? "#f97316"
              : log.kind === "success"
                ? "#10b981"
                : "#22d3ee";
        return (
          <div
            key={log.id}
            style={{
              flexShrink: 0,
              background: `linear-gradient(90deg, ${c}11, transparent)`,
              borderLeft: `2px solid ${c}`,
              padding: "0.5rem 0.75rem",
              borderRadius: "0 6px 6px 0",
              fontFamily: "JetBrains Mono",
              fontSize: "0.55rem",
              lineHeight: 1.5,
              color: "rgba(255,255,255,0.75)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <span style={{ color: c, fontWeight: 700 }}>[{log.agent}]</span>
              <span style={{ color: "rgba(255,255,255,0.3)" }}>{log.ts}</span>
            </div>
            <div>{log.text}</div>
          </div>
        );
      })}
    </div>
  );
}

function CompactMetrics( { topology }: { topology: any } ) {
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
    <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 12, overflowY: "auto" }}>
      {/* Top Level KPIs */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        <div style={{ background: "rgba(255,255,255,0.03)", padding: "8px 12px", borderRadius: 8, borderLeft: "2px solid #ef4444" }}>
          <div style={{ fontSize: "0.45rem", fontFamily: "JetBrains Mono", color: "rgba(255,255,255,0.4)" }}>IMPACTED SERVICES</div>
          <div style={{ fontSize: "1rem", fontFamily: "Space Grotesk", color: "#ef4444", fontWeight: 700 }}>2 Critical</div>
        </div>
        <div style={{ background: "rgba(255,255,255,0.03)", padding: "8px 12px", borderRadius: 8, borderLeft: "2px solid #22d3ee" }}>
          <div style={{ fontSize: "0.45rem", fontFamily: "JetBrains Mono", color: "rgba(255,255,255,0.4)" }}>ACTIVE ORCHESTRATIONS</div>
          <div style={{ fontSize: "1rem", fontFamily: "Space Grotesk", color: "#22d3ee", fontWeight: 700 }}>3 Routines</div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr", gap: 8, padding: "0 10px 6px",
        borderBottom: "1px solid rgba(255,255,255,0.1)", fontSize: "0.45rem", fontFamily: "Space Grotesk", color: "rgba(255,255,255,0.4)" }}>
        <span>CORE SERVICE</span><span>LATENCY P99</span><span>CPU SATURATION</span>
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

  useEffect(() => {
    const t = setInterval(() => {
      setSteps(s => s.map(st => st.id === "R-3" ? { ...st, status: "completed", time: "4.5s" } : st.id === "R-4" ? { ...st, status: "active", time: "running" } : st));
    }, 4500);
    return () => clearInterval(t);
  }, []);

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 12, overflow: "hidden" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid rgba(255,255,255,0.05)", paddingBottom: 8 }}>
        <span style={{ fontSize: "0.55rem", fontFamily: "JetBrains Mono", color: "rgba(255,255,255,0.5)" }}>ORCHESTRATOR WORKFLOW: <span style={{ color: "#fff" }}>INC-MITIGATION-Alpha</span></span>
        <span style={{ fontSize: "0.45rem", fontFamily: "JetBrains Mono", color: "#22d3ee", border: "1px solid rgba(34,211,238,0.3)", padding: "2px 6px", borderRadius: 4, background: "rgba(34,211,238,0.1)" }}>EXECUTING</span>
      </div>
      
      <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 10, padding: "4px 4px" }} className="scrollbar-thin scrollbar-thumb-cyan-500/20 scrollbar-track-transparent">
        {steps.map((st, i) => (
          <div key={st.id} style={{ display: "flex", gap: 12, opacity: st.status === 'pending' ? 0.35 : 1 }}>
            
            {/* Timeline Line */}
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
              <div style={{ 
                width: 16, height: 16, borderRadius: "2px", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
                background: st.status === 'completed' ? "rgba(16,185,129,0.15)" : st.status === 'active' ? "rgba(34,211,238,0.15)" : "transparent",
                border: `1px solid ${st.status === 'completed' ? "#10b981" : st.status === 'active' ? "#22d3ee" : "rgba(255,255,255,0.15)"}`,
                transform: "rotate(45deg)"
              }}>
                <div style={{ transform: "rotate(-45deg)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  {st.status === 'completed' && <CheckCircle style={{ width: 8, height: 8, color: "#10b981" }} />}
                  {st.status === 'active' && <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#22d3ee", animation: "pulse-cyan 1.5s infinite" }} />}
                </div>
              </div>
              {i < steps.length -1 && <div style={{ width: 1, flex: 1, background: st.status === 'completed' ? "#10b981" : st.status === 'active' ? "rgba(34,211,238,0.3)" : "rgba(255,255,255,0.1)", minHeight: 18 }} />}
            </div>

            {/* Content block */}
            <div style={{ flex: 1, paddingBottom: 16 }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 2 }}>
                <span style={{ fontSize: "0.45rem", fontFamily: "Space Grotesk", color: st.status === 'completed' ? "#10b981" : st.status === 'active' ? "#22d3ee" : "rgba(255,255,255,0.4)", letterSpacing: "0.1em" }}>
                  PHASE: {st.phase}
                </span>
                <span style={{ fontSize: "0.45rem", fontFamily: "JetBrains Mono", color: "rgba(255,255,255,0.3)" }}>{st.time}</span>
              </div>
              <div style={{ fontSize: "0.6rem", fontFamily: "Space Grotesk", color: st.status === 'completed' ? "rgba(255,255,255,0.7)" : "#fff" }}>
                {st.text}
              </div>
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

// â”€â”€ Main Page â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export default function IncidentCommandCenter() {
  const { state } = usePlatform();
  const reasoning = useReasoningLog();
  const { topology, criticalCount, incidents } = state;
  const activeIncident = incidents[0] || { title: "INC-2049: Latency Cascade", severity: "critical", id: "INC-2049" };

  return (
    <div
      style={{
        height: "calc(100vh - 128px)",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        gap: 12,
        minHeight: 0,
        paddingRight: 4,
      }}
    >
      
      {/* â”€â”€ Top Command Bar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ width: 44, height: 44, background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.4)", borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 0 20px rgba(239, 68, 68, 0.2)" }}>
            <AlertTriangle style={{ width: 22, height: 22, color: "#ef4444" }} className="animate-pulse" />
          </div>
          <div>
            <h1 style={{ fontSize: "1.5rem", fontWeight: 800, fontFamily: "Space Grotesk", color: "#ef4444", textShadow: "0 0 16px rgba(239, 68, 68, 0.5)", margin: 0, lineHeight: 1.1 }}>
              AI WAR ROOM
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

      <div
        style={{
          flex: 1,
          minHeight: 0,
          display: "grid",
          gridTemplateColumns: "1.1fr 1.3fr 1fr",
          gap: 12,
          overflow: "hidden",
        }}
      >
        {/* LEFT PANEL: Cognitive Stream — fixed height, internal scroll only */}
        <div
          style={{
            ...P,
            display: "flex",
            flexDirection: "column",
            padding: "0.75rem 1rem",
            overflow: "hidden",
            minHeight: 0,
            height: "100%",
          }}
        >
          <div style={{ ...PH, flexShrink: 0, justifyContent: "space-between" }}>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <Cpu size={14} color="#22d3ee" /> Cognitive Engine Stream
            </span>
            <span style={{ fontSize: "0.45rem", fontFamily: "JetBrains Mono", opacity: 0.45 }}>
              {reasoning.length} live
            </span>
          </div>
          <CognitiveStream />
        </div>

        {/* CENTER PANEL: Incident Remediation Timeline */}
        <div style={{ ...P, display: "flex", flexDirection: "column", padding: "0.75rem 1rem", minHeight: 0, overflow: "hidden", height: "100%" }}>
          <div style={PH}><Terminal size={14} color="#10b981" /> Remediation Orchestration</div>
          <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 16, marginTop: 8, overflow: "hidden" }}>
             <RemediationTimeline />
             
             {/* Sub-panel in center for live action log */}
             <div style={{ height: 120, background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.05)", borderRadius: 8, padding: "0.5rem", overflowY: "auto", fontFamily: "JetBrains Mono", fontSize: "0.5rem", color: "rgba(255,255,255,0.4)", flexShrink: 0 }}>
               <div style={{ color: "#22d3ee", marginBottom: 4 }}>$ neural-agent orchestrate --incident INC-2049</div>
               <div>[SUCCESS] Lock acquired on api-gateway-0</div>
               <div>[INFO] Draining 1402 active sessions...</div>
               <div>[SUCCESS] Postgres connection pool flushed.</div>
               <div style={{ color: "#10b981" }}>[ACTIVE] Awaiting replica health validation (6/6 pending)</div>
             </div>
          </div>
        </div>

        {/* RIGHT PANEL: Compact Metrics & Forecast */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10, minHeight: 0, overflow: "hidden", height: "100%" }}>
          <div style={{ ...P, flex: 1, display: "flex", flexDirection: "column", padding: "0.75rem 1rem", minHeight: 0, overflow: "hidden" }}>
            <div style={PH}><Activity size={14} color="#f97316" /> Compact Metrics</div>
            <CompactMetrics topology={topology} />
          </div>
          
          <div style={{ ...P, padding: "1rem", flexShrink: 0 }}>
            <div style={PH}><Crosshair size={14} color="#eab308" /> AI Consensus & Recovery Forecast</div>
            <ConsensusForecast />
          </div>
        </div>
      </div>

    </div>
  );
}







