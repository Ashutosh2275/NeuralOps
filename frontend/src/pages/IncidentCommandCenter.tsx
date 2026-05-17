import React, {
  useEffect,
  useRef,
  useState,
  useCallback,
  useMemo,
} from "react";
import { useWebSocket, WSEvent } from "../hooks/useWebSocket";
import { motion, AnimatePresence } from "framer-motion";
import {
  Activity,
  ShieldAlert,
  Cpu,
  Network,
  Zap,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  Radio,
  Server,
  Crosshair,
} from "lucide-react";

/* ─── Types ──────────────────────────────────────────────────────────────── */
interface IncidentEvent {
  id: string;
  type: string;
  severity: "critical" | "high" | "medium" | "low";
  timestamp: number;
  payload: Record<string, unknown>;
  aiReasoning?: string;
}

interface RemediationStep {
  id: number;
  label: string;
  status: "done" | "active" | "pending";
}

interface BlastNode {
  service: string;
  impact: "critical" | "high" | "medium" | "low";
  affectedPods: number;
}

/* ─── Severity helpers ───────────────────────────────────────────────────── */
const severityColor: Record<string, string> = {
  critical: "#ef4444",
  high: "#f97316",
  medium: "#eab308",
  low: "#22c55e",
};
const severityBorder: Record<string, string> = {
  critical: "border-red-500/50 glow-border-danger",
  high: "border-orange-500/50",
  medium: "border-yellow-500/50",
  low: "border-green-500/50",
};

function classifySeverity(type: string): IncidentEvent["severity"] {
  if (type.includes("critical") || type.includes("crash")) return "critical";
  if (type.includes("failure") || type.includes("cascade")) return "high";
  if (type.includes("latency") || type.includes("memory")) return "medium";
  return "low";
}

/* ─── AI Reasoning Feed ─────────────────────────────────────────────────── */
const REASONING_SNIPPETS = [
  "Detected memory pressure escalation across 12 pods. Initiating correlated RCA...",
  "Blast radius confirmed: API gateway → payment-service → database. Cascade depth 3.",
  "Remediation confidence: 94%. Recommending replica scale-up + connection pool flush.",
  "Anomaly pattern matches historical incident #1047 (2025-11-03). TTR estimate: 4.2min.",
  "Network partition isolated to availability zone B. Health propagation contained.",
  "Self-healing action triggered: pod eviction for api-server-2. Monitoring recovery...",
  "CPU utilisation normalising after throttling injection. SLA compliance: 99.1%.",
  "Ollama inference latency 1.2s — RTX 3050 Ti GPU utilisation at 78%.",
];

const AIReasoningFeed: React.FC<{ events: IncidentEvent[] }> = ({ events }) => {
  const [lines, setLines] = useState<{ id: number; text: string }[]>([]);
  const lineId = useRef(0);

  useEffect(() => {
    const interval = setInterval(() => {
      const text = REASONING_SNIPPETS[Math.floor(Math.random() * REASONING_SNIPPETS.length)];
      setLines((prev) => [{ id: lineId.current++, text }, ...prev].slice(0, 15));
    }, 3500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col gap-2 overflow-y-hidden flex-1 pr-1 relative">
      <div className="absolute inset-x-0 bottom-0 h-12 bg-gradient-to-t from-sentinel-900 to-transparent z-10 pointer-events-none" />
      <AnimatePresence>
        {lines.map((line, i) => (
          <motion.div
            key={line.id}
            initial={{ opacity: 0, x: -20, height: 0 }}
            animate={{ opacity: 1 - (i * 0.08), x: 0, height: "auto" }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ type: "spring", stiffness: 400, damping: 25 }}
            className="bg-sentinel-900/80 backdrop-blur-sm border-l-2 border-sentinel-accent/50 rounded-r p-2.5 text-xs font-mono text-sentinel-accent shadow-[0_0_10px_rgba(34,211,238,0.05)]"
          >
            <span className="text-white/50 mr-2">[{new Date().toLocaleTimeString()}]</span>
            <span className="text-sentinel-accent/80 mr-1 animate-pulse">●</span>
            {line.text}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

/* ── Blast Radius Panel ─────────────────────────────────────────────────── */
const BlastRadiusPanel: React.FC<{ nodes: BlastNode[]; eventCount: number }> = ({
  nodes,
  eventCount,
}) => (
  <div className="flex flex-col gap-4 h-full">
    <motion.div 
      initial={{ scale: 0.95, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className="glass-panel rounded-xl p-4 relative overflow-hidden"
    >
      <div className="absolute top-0 right-0 w-24 h-24 bg-red-500/10 rounded-full blur-2xl pointer-events-none" />
      <div className="flex items-center gap-2 text-red-400 font-display font-semibold text-sm mb-2 uppercase tracking-widest glow-text-accent text-shadow-red">
        <AlertTriangle size={16} /> Critical Impact
      </div>
      <div className="text-4xl font-bold text-white font-sans tabular-nums">
        {nodes.filter((n) => n.impact === "critical").length} 
        <span className="text-lg text-gray-500 font-normal ml-2">Services</span>
      </div>
      <div className="text-xs text-gray-400 mt-2 flex items-center gap-2">
        <Activity size={12} className="text-sentinel-accent animate-pulse" />
        {eventCount} anomaly events in last 60s
      </div>
    </motion.div>

    <div className="flex flex-col gap-2 overflow-y-auto pr-2 custom-scrollbar flex-1">
      <AnimatePresence>
        {nodes.map((n, i) => (
          <motion.div
            key={n.service}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            className={`glass-panel border-l-4 rounded-lg p-3 ${
              n.impact === 'critical' ? 'border-l-red-500 bg-red-500/5' :
              n.impact === 'high' ? 'border-l-orange-500 bg-orange-500/5' :
              n.impact === 'medium' ? 'border-l-yellow-500 bg-yellow-500/5' :
              'border-l-green-500 bg-green-500/5'
            }`}
          >
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-200 font-sans">{n.service}</span>
              <span
                className="text-[10px] px-2 py-0.5 rounded font-mono uppercase tracking-wider"
                style={{
                  background: severityColor[n.impact] + "22",
                  color: severityColor[n.impact],
                  border: `1px solid ${severityColor[n.impact]}44`
                }}
              >
                {n.impact}
              </span>
            </div>
            <div className="flex justify-between items-end">
              <div className="text-xs text-gray-400">{n.affectedPods} pods affected</div>
              <div className="w-24 h-1.5 bg-sentinel-950 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ 
                    width: n.impact === "critical" ? "90%" : n.impact === "high" ? "65%" : n.impact === "medium" ? "40%" : "15%",
                  }}
                  transition={{ duration: 1, ease: "easeOut" }}
                  className="h-full rounded-full"
                  style={{ background: severityColor[n.impact], boxShadow: `0 0 10px ${severityColor[n.impact]}` }}
                />
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  </div>
);

/* ─── D3-lite canvas ─────────────────────────── */
const MOCK_SERVICES = [
  "api-gateway",
  "auth-service",
  "payment-service",
  "catalog-service",
  "inventory-service",
  "database",
  "redis-cache",
];

const InfraMap: React.FC<{ blastNodes: BlastNode[]; connected: boolean }> = ({
  blastNodes,
  connected,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>();

  const blastMap = useMemo(
    () => new Map(blastNodes.map((n) => [n.service, n.impact])),
    [blastNodes]
  );

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;
    let tick = 0;

    // Resize handler for sharp canvas
    const resize = () => {
      const parent = canvas.parentElement;
      if (parent) {
        canvas.width = parent.clientWidth * window.devicePixelRatio;
        canvas.height = parent.clientHeight * window.devicePixelRatio;
        ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
      }
    };
    resize();
    window.addEventListener('resize', resize);

    const positions = MOCK_SERVICES.map((_, i) => {
      const angle = ((i / MOCK_SERVICES.length) * Math.PI * 2) - Math.PI / 2;
      return { angle };
    });

    const draw = () => {
      tick++;
      const w = canvas.width / window.devicePixelRatio;
      const h = canvas.height / window.devicePixelRatio;
      ctx.clearRect(0, 0, w, h);
      
      const cx = w / 2;
      const cy = h / 2;
      const r = Math.min(w, h) * 0.35;

      const currentPos = positions.map(p => ({
        x: cx + r * Math.cos(p.angle + (tick * 0.001)),
        y: cy + r * Math.sin(p.angle + (tick * 0.001))
      }));

      // Draw Grid Background
      ctx.strokeStyle = "rgba(34,211,238,0.03)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let i = 0; i < w; i += 40) { ctx.moveTo(i, 0); ctx.lineTo(i, h); }
      for (let i = 0; i < h; i += 40) { ctx.moveTo(0, i); ctx.lineTo(w, i); }
      ctx.stroke();

      // Draw Edges (Data flow)
      currentPos.forEach((from, i) => {
        currentPos.forEach((to, j) => {
          if (i >= j) return;
          const dist = Math.hypot(from.x - to.x, from.y - to.y);
          if (dist > r * 1.5) return;
          
          const alpha = 0.1 + 0.1 * Math.sin(tick / 20 + i);
          
          // Edge glow
          ctx.strokeStyle = `rgba(34,211,238,${alpha})`;
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.moveTo(from.x, from.y);
          ctx.lineTo(to.x, to.y);
          ctx.stroke();
          
          // Flowing packet
          if ((tick + i * 20) % 100 < 5) {
             const progress = ((tick + i * 20) % 100) / 100;
             const px = from.x + (to.x - from.x) * progress;
             const py = from.y + (to.y - from.y) * progress;
             ctx.fillStyle = "#22d3ee";
             ctx.beginPath();
             ctx.arc(px, py, 2, 0, Math.PI * 2);
             ctx.fill();
             ctx.shadowColor = "#22d3ee";
             ctx.shadowBlur = 10;
          }
        });
      });
      ctx.shadowBlur = 0; // reset

      // Draw Nodes
      MOCK_SERVICES.forEach((svc, i) => {
        const { x, y } = currentPos[i];
        const impact = blastMap.get(svc);
        const color = impact ? severityColor[impact] : "#22d3ee";
        const pulse = impact === "critical" ? 8 + 4 * Math.sin(tick / 8) : 0;
        const nodeR = 14 + pulse;

        // Outer Glow
        const grd = ctx.createRadialGradient(x, y, 0, x, y, nodeR * 2.5);
        grd.addColorStop(0, color + "66");
        grd.addColorStop(1, color + "00");
        ctx.fillStyle = grd;
        ctx.beginPath();
        ctx.arc(x, y, nodeR * 2.5, 0, Math.PI * 2);
        ctx.fill();

        // Node Body
        ctx.fillStyle = color + "22";
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(x, y, nodeR, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();

        // Inner Core
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();

        // Label
        ctx.fillStyle = "#e2e8f0";
        ctx.font = "10px 'JetBrains Mono'";
        ctx.textAlign = "center";
        ctx.fillText(svc.replace("-service", ""), x, y + nodeR + 16);
      });

      // Center hub
      ctx.fillStyle = connected ? "rgba(34,211,238,0.15)" : "rgba(107,114,128,0.15)";
      ctx.strokeStyle = connected ? "#22d3ee" : "#6b7280";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(cx, cy, 22, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      
      // Hub pulse
      if (connected) {
        ctx.strokeStyle = `rgba(34,211,238,${0.5 * Math.max(0, Math.sin(tick/15))})`;
        ctx.beginPath();
        ctx.arc(cx, cy, 22 + (tick % 40), 0, Math.PI * 2);
        ctx.stroke();
      }

      ctx.fillStyle = connected ? "#22d3ee" : "#94a3b8";
      ctx.font = "bold 10px 'JetBrains Mono'";
      ctx.textAlign = "center";
      ctx.fillText("CORE", cx, cy + 3);

      animRef.current = requestAnimationFrame(draw);
    };

    draw();
    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
      window.removeEventListener('resize', resize);
    };
  }, [blastMap, connected]);

  return (
    <div className="absolute inset-0">
      <canvas
        ref={canvasRef}
        className="w-full h-full"
        style={{ display: "block" }}
      />
    </div>
  );
};

/* ─── KPI Strip ──────────────────────────────────────────────────────────── */
const KPIStrip: React.FC<{
  connected: boolean;
  eventCount: number;
  criticalCount: number;
  activeNodes: number;
}> = ({ connected, eventCount, criticalCount, activeNodes }) => {
  const [latency, setLatency] = React.useState(0.7);
  React.useEffect(() => {
    const t = setInterval(() => setLatency(+(0.4 + Math.random() * 1.2).toFixed(1)), 1800);
    return () => clearInterval(t);
  }, []);

  const kpis = [
    { icon: <Server size={16} />, label: "Active Nodes",  value: activeNodes,           color: "text-sentinel-accent", border: "border-sentinel-accent/20", bg: "rgba(34,211,238,0.04)" },
    { icon: <Zap size={16} />,    label: "Stream Rate",   value: `${eventCount}/s`,      color: "text-yellow-400",      border: "border-yellow-500/20",     bg: "rgba(234,179,8,0.04)"  },
    { icon: <AlertTriangle size={16} />, label: "Critical",value: criticalCount,         color: criticalCount > 0 ? "text-red-400" : "text-green-400", border: criticalCount > 0 ? "border-red-500/30" : "border-green-500/20", bg: criticalCount > 0 ? "rgba(239,68,68,0.06)" : "rgba(16,185,129,0.04)" },
    { icon: <TrendingUp size={16} />, label: "SLA Target", value: "99.9%",              color: "text-sentinel-success", border: "border-green-500/20",      bg: "rgba(16,185,129,0.04)" },
    { icon: <Cpu size={16} />,    label: "AI Engine",     value: "ONLINE",              color: "text-purple-400",       border: "border-purple-500/20",     bg: "rgba(168,85,247,0.04)" },
    { icon: <Network size={16} />,label: "P99 Latency",   value: `${latency}ms`,        color: latency > 1 ? "text-orange-400" : "text-blue-400", border: "border-blue-500/20", bg: "rgba(59,130,246,0.04)" },
  ];

  return (
    <div className="grid grid-cols-6 gap-3 mb-6">
      {kpis.map((k, i) => (
        <motion.div
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.07 }}
          key={i}
          whileHover={{ y: -2 }}
          className={`glass-panel rounded-xl p-3.5 flex flex-col gap-1.5 relative overflow-hidden border ${k.border} holo-card`}
          style={{ background: `linear-gradient(135deg, ${k.bg} 0%, transparent 60%)` }}
        >
          <div className="flex items-center justify-between">
            <span className="text-[8px] font-mono text-gray-500 uppercase tracking-[0.15em]">{k.label}</span>
            <span className={`${k.color} opacity-40`}>{k.icon}</span>
          </div>
          <motion.span
            key={String(k.value)}
            initial={{ y: 6, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className={`text-xl font-display font-black tabular-nums leading-none ${k.color}`}
          >
            {k.value}
          </motion.span>
          <div className={`absolute bottom-0 left-0 h-px w-full bg-gradient-to-r from-transparent ${k.color.replace("text-", "via-").replace("-400", "-400/40").replace("-500", "-500/40")} to-transparent`} />
        </motion.div>
      ))}
    </div>
  );
};

/* ─── Main Page ──────────────────────────────────────────────────────────── */
export default function IncidentCommandCenter() {
  const { connected, events } = useWebSocket();
  const [incidents, setIncidents] = useState<IncidentEvent[]>([]);
  const [blastNodes, setBlastNodes] = useState<BlastNode[]>(() =>
    MOCK_SERVICES.map((svc, i) => ({
      service: svc,
      impact: (["critical", "high", "high", "medium", "medium", "low", "low"] as const)[i],
      affectedPods: [12, 8, 9, 5, 4, 2, 1][i],
    }))
  );
  const activeNodes = 507;

  const criticalCount = useMemo(
    () => blastNodes.filter((n) => n.impact === "critical").length,
    [blastNodes]
  );

  useEffect(() => {
    const relevant = events.filter(
      (e) =>
        e.type === "cascading_failure" ||
        e.type === "health_propagation" ||
        e.type === "node_health" ||
        e.type === "edge_health"
    );
    setIncidents((prev) => {
      const mapped = relevant.map((e) => ({
        id: Math.random().toString(36).slice(2),
        type: e.type,
        severity: classifySeverity(e.type),
        timestamp: Date.now(),
        payload: e.payload,
      }));
      return [...mapped, ...prev].slice(0, 50);
    });
  }, [events]);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <header className="flex justify-between items-end mb-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center justify-center glow-border-danger">
            <Crosshair size={24} className="text-red-500 animate-pulse-slow" />
          </div>
          <div>
            <h1 className="text-3xl font-display font-bold text-white tracking-tight uppercase glow-text-accent">
              Incident Command
            </h1>
            <p className="text-sm text-sentinel-accent/70 font-sans tracking-widest uppercase mt-1 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-sentinel-accent animate-pulse" />
              Autonomous Response Active
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4 glass-panel px-4 py-2 rounded-lg">
          <span className="text-xs text-gray-400 font-mono tracking-widest">
            SYS.TIME // {new Date().toLocaleTimeString()}
          </span>
          <div className="w-px h-4 bg-gray-700" />
          <span
            className={`flex items-center gap-2 text-xs font-sans tracking-widest uppercase ${
              connected ? "text-sentinel-success" : "text-sentinel-danger"
            }`}
          >
            <span
              className={`inline-block w-2 h-2 rounded-full ${
                connected ? "bg-sentinel-success shadow-[0_0_8px_#10b981]" : "bg-sentinel-danger shadow-[0_0_8px_#ef4444]"
              }`}
            />
            {connected ? "LINK ESTABLISHED" : "LINK SEVERED"}
          </span>
        </div>
      </header>

      <KPIStrip
        connected={connected}
        eventCount={events.length || 24} // Mock some data if events is empty for demo
        criticalCount={criticalCount}
        activeNodes={activeNodes}
      />

      <div className="grid grid-cols-12 gap-6 flex-1 min-h-0 pb-6">
        {/* Left — AI Reasoning */}
        <div className="col-span-3 flex flex-col gap-4 h-full">
          <div className="glass-panel rounded-xl p-5 flex-1 flex flex-col overflow-hidden relative group">
            <div className="absolute inset-0 bg-gradient-to-br from-sentinel-accent/5 to-transparent pointer-events-none" />
            <div className="flex items-center gap-3 mb-4 border-b border-sentinel-700/50 pb-3">
              <div className="p-1.5 rounded bg-sentinel-accent/10 border border-sentinel-accent/30 text-sentinel-accent">
                <Cpu size={16} />
              </div>
              <h2 className="text-xs font-display font-bold text-white uppercase tracking-widest">
                Cognitive Stream
              </h2>
            </div>
            <AIReasoningFeed events={incidents} />
          </div>
        </div>

        {/* Center — Infra State Map */}
        <div className="col-span-6 glass-panel rounded-xl p-1 flex flex-col relative overflow-hidden">
          <div className="absolute top-4 left-4 z-10 flex items-center gap-3 glass-panel px-3 py-1.5 rounded-lg border border-sentinel-700/50">
             <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
              </span>
              <span className="text-[10px] text-gray-300 font-sans uppercase tracking-widest">Global Topology Map</span>
          </div>
          <div className="flex-1 relative w-full h-full bg-sentinel-950 rounded-lg overflow-hidden border border-sentinel-900 shadow-inner">
             <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(34,211,238,0.05)_0%,transparent_70%)] pointer-events-none" />
             <InfraMap blastNodes={blastNodes} connected={connected} />
          </div>
        </div>

        {/* Right — Blast Radius */}
        <div className="col-span-3 h-full">
          <BlastRadiusPanel nodes={blastNodes} eventCount={events.length || 15} />
        </div>
      </div>
    </div>
  );
}
