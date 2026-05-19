import { useEffect, useState, useMemo } from "react";
import AdvancedTopologyVisualization from "../components/topology/AdvancedTopologyVisualization";
import { usePlatform } from "../contexts/PlatformContext";
import { Network, Activity, ShieldAlert, Cpu, X, Menu, Settings, Database, RefreshCw, Zap, TrendingUp, AlertTriangle, CheckCircle, Terminal } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface NodeDetails {
  id: string;
  name: string;
  kind?: string;
  health?: "healthy" | "degraded" | "critical";
  cpu_percent?: number;
  memory_percent?: number;
  uptime_percent?: number;
  incident_count?: number;
}

const MOCK_NODES = [
  { id: "api-gateway", name: "api-gateway", kind: "Deployment", health: "healthy" as const, cpu_percent: 42, memory_percent: 61, uptime_percent: 99.98, incident_count: 0 },
  { id: "auth-service", name: "auth-service", kind: "Deployment", health: "healthy" as const, cpu_percent: 28, memory_percent: 45, uptime_percent: 99.95, incident_count: 0 },
  { id: "payment-service", name: "payment-service", kind: "Deployment", health: "healthy" as const, cpu_percent: 34, memory_percent: 55, uptime_percent: 99.92, incident_count: 0 },
  { id: "checkout-service", name: "checkout-service", kind: "Deployment", health: "healthy" as const, cpu_percent: 31, memory_percent: 48, uptime_percent: 99.99, incident_count: 0 },
  { id: "inventory-service", name: "inventory-service", kind: "Deployment", health: "healthy" as const, cpu_percent: 19, memory_percent: 38, uptime_percent: 99.97, incident_count: 0 },
  { id: "recommendation-engine", name: "recommendation-engine", kind: "Deployment", health: "healthy" as const, cpu_percent: 52, memory_percent: 72, uptime_percent: 99.85, incident_count: 0 },
  { id: "postgres-primary", name: "postgres-primary", kind: "StatefulSet", health: "healthy" as const, cpu_percent: 45, memory_percent: 68, uptime_percent: 99.99, incident_count: 0 },
  { id: "redis-cache", name: "redis-cache", kind: "StatefulSet", health: "healthy" as const, cpu_percent: 23, memory_percent: 40, uptime_percent: 99.99, incident_count: 0 }
];

const MOCK_EDGES = [
  { source: "api-gateway", target: "auth-service", edge_type: "gRPC", confidence: 0.98, health: "healthy" },
  { source: "api-gateway", target: "checkout-service", edge_type: "gRPC", confidence: 0.95, health: "healthy" },
  { source: "checkout-service", target: "payment-service", edge_type: "HTTP", confidence: 0.92, health: "healthy" },
  { source: "checkout-service", target: "inventory-service", edge_type: "gRPC", confidence: 0.97, health: "healthy" },
  { source: "checkout-service", target: "recommendation-engine", edge_type: "HTTP", confidence: 0.88, health: "healthy" },
  { source: "payment-service", target: "postgres-primary", edge_type: "TCP", confidence: 0.99, health: "healthy" },
  { source: "inventory-service", target: "postgres-primary", edge_type: "TCP", confidence: 0.94, health: "healthy" },
  { source: "recommendation-engine", target: "redis-cache", edge_type: "TCP", confidence: 0.91, health: "healthy" }
];

export default function Topology() {
  const { state } = usePlatform();
  const [selectedNode, setSelectedNode] = useState<NodeDetails | null>(null);
  const [showControls, setShowControls] = useState(false);
  const [localNodeMetrics, setLocalNodeMetrics] = useState<Record<string, { cpu: number; mem: number; history: number[] }>>({});
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // 1. Universal State Sync — Sync with PlatformContext incidents
  const { activeIncidents, rootCauseNode, blastRadiusNodes } = useMemo(() => {
    const active = state.incidents.filter(i => i.status !== "resolved");
    let rc: string | null = null;
    let br: string[] = [];
    
    if (active.length > 0) {
      // Find first incident with root service
      const mainIncident = active.find(i => i.root_service);
      if (mainIncident && mainIncident.root_service) {
        rc = mainIncident.root_service;
        // Build blast radius nodes based on connections
        if (rc === "postgres-primary") {
          br = ["postgres-primary", "payment-service", "checkout-service", "api-gateway"];
        } else if (rc === "payment-service") {
          br = ["payment-service", "checkout-service", "api-gateway"];
        } else {
          br = [rc];
        }
      }
    }
    return { activeIncidents: active, rootCauseNode: rc, blastRadiusNodes: br };
  }, [state.incidents]);

  // 2. Generate local dynamic node telemetry
  useEffect(() => {
    // Initialize
    const initial: Record<string, { cpu: number; mem: number; history: number[] }> = {};
    MOCK_NODES.forEach(n => {
      initial[n.id] = {
        cpu: n.cpu_percent,
        mem: n.memory_percent,
        history: Array.from({ length: 15 }, () => 20 + Math.random() * 50)
      };
    });
    setLocalNodeMetrics(initial);

    // Live oscillation tick
    const interval = setInterval(() => {
      setLocalNodeMetrics(prev => {
        const next = { ...prev };
        Object.keys(next).forEach(id => {
          const nodeInfo = next[id];
          if (!nodeInfo) return;
          
          let targetCpu = 30 + Math.random() * 40;
          let targetMem = 40 + Math.random() * 30;

          // If node is root cause or in blast radius, elevate metrics
          if (id === rootCauseNode) {
            targetCpu = 85 + Math.random() * 12;
            targetMem = 91 + Math.random() * 6;
          } else if (blastRadiusNodes.includes(id)) {
            targetCpu = 65 + Math.random() * 20;
            targetMem = 75 + Math.random() * 15;
          }

          const newCpu = Math.max(10, Math.min(100, nodeInfo.cpu + (targetCpu - nodeInfo.cpu) * 0.25));
          const newMem = Math.max(10, Math.min(100, nodeInfo.mem + (targetMem - nodeInfo.mem) * 0.25));
          const newHistory = [...nodeInfo.history.slice(1), newCpu];

          next[id] = { cpu: newCpu, mem: newMem, history: newHistory };
        });
        return next;
      });
    }, 2500);

    return () => clearInterval(interval);
  }, [rootCauseNode, blastRadiusNodes]);

  // 3. Assemble dynamic graph data combining backend and simulated states
  const finalGraph = useMemo(() => {
    const nodesSource = (state.topology && state.topology.nodes.length > 0 ? state.topology.nodes : MOCK_NODES) as any[];
    const edgesSource = (state.topology && state.topology.edges.length > 0 ? state.topology.edges : MOCK_EDGES) as any[];

    const mappedNodes = nodesSource.map(n => {
      const live = localNodeMetrics[n.id];
      let healthState: "healthy" | "degraded" | "critical" = "healthy";

      if (n.id === rootCauseNode) {
        healthState = "critical";
      } else if (blastRadiusNodes.includes(n.id)) {
        healthState = "degraded";
      } else if (n.health === "critical" || n.health === "degraded" || n.health === "warning") {
        healthState = n.health === "critical" ? "critical" : "degraded";
      }

      return {
        id: n.id,
        name: n.name || n.id,
        kind: n.kind || "Deployment",
        health: healthState,
        cpu_percent: live ? live.cpu : (n.cpu_percent || 30),
        memory_percent: live ? live.mem : (n.memory_percent || 45),
        uptime_percent: n.uptime_percent || 99.9,
        incident_count: n.id === rootCauseNode ? 1 : 0
      };
    });

    const mappedEdges = edgesSource.map(e => {
      const isAffected = blastRadiusNodes.includes(e.source) && blastRadiusNodes.includes(e.target);
      return {
        source: e.source,
        target: e.target,
        edge_type: e.edge_type || "gRPC",
        confidence: e.confidence || 0.95,
        health: isAffected ? "degraded" : "healthy",
        weight: isAffected ? 3 : 1,
        traffic_rate: isAffected ? 400 + Math.random() * 500 : 80 + Math.random() * 120
      };
    });

    return {
      nodes: mappedNodes,
      edges: mappedEdges,
      node_count: mappedNodes.length,
      edge_count: mappedEdges.length
    };
  }, [state.topology, localNodeMetrics, rootCauseNode, blastRadiusNodes]);

  // Node Click Handlers
  const handleNodeClick = (node: any) => {
    setSelectedNode(node);
  };

  const handleAction = async (actionType: string) => {
    if (!selectedNode) return;
    setActionLoading(actionType);
    setActionSuccess(null);
    // Simulate orchestration request latency
    await new Promise(r => setTimeout(r, 1600));
    setActionLoading(null);
    setActionSuccess(`Successfully dispatched ${actionType} instruction to cluster scheduler.`);
    setTimeout(() => setActionSuccess(null), 4000);
  };

  // Sparkline builder helper
  const getSparklinePath = (history: number[]) => {
    if (!history || history.length === 0) return "";
    const width = 240;
    const height = 40;
    const maxVal = 100;
    const step = width / (history.length - 1);
    
    return history.map((val, index) => {
      const x = index * step;
      const y = height - (val / maxVal) * height;
      return `${index === 0 ? "M" : "L"} ${x} ${y}`;
    }).join(" ");
  };

  return (
    <div className="w-full h-[calc(100vh-140px)] flex flex-col overflow-hidden rounded-2xl border border-sentinel-700/30 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 shadow-2xl relative">
      
      {/* Topology Header Panel */}
      <div className="h-12 bg-black/40 border-b border-sentinel-accent/20 flex items-center justify-between px-6 flex-shrink-0 z-10">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 bg-sentinel-accent/15 border border-sentinel-accent/30 rounded flex items-center justify-center">
            <Network size={15} className="text-sentinel-accent" />
          </div>
          <div>
            <span className="text-xs font-mono font-bold text-white tracking-widest uppercase">Neural Topology Map</span>
            <span className="hidden sm:inline-block text-[9px] font-mono text-gray-500 uppercase tracking-widest ml-3 border-l border-white/10 pl-3">
              Cluster Orchestration Engine v2.4
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Universal Sync Alert Badge */}
          {activeIncidents.length > 0 && (
            <motion.div 
              animate={{ opacity: [0.6, 1, 0.6] }}
              transition={{ repeat: Infinity, duration: 1.8 }}
              className="flex items-center gap-1.5 text-[9px] font-mono uppercase bg-red-950/40 border border-red-500/40 px-2 py-0.5 rounded text-red-400"
            >
              <ShieldAlert size={11} className="text-red-400" />
              <span>{activeIncidents.length} Active Incidents</span>
            </motion.div>
          )}

          {/* Connected state */}
          <span className={`flex items-center gap-1.5 text-[9px] font-mono uppercase px-2 py-0.5 rounded ${state.wsConnected ? 'text-green-400 bg-green-500/10 border border-green-500/20' : 'text-red-400 bg-red-500/10 border border-red-500/20'}`}>
            <span className={`inline-block w-1 h-1 rounded-full ${state.wsConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
            {state.wsConnected ? 'LIVE FEED' : 'OFFLINE'}
          </span>

          <button
            onClick={() => setShowControls(!showControls)}
            className="p-1.5 hover:bg-white/5 rounded border border-sentinel-700/40 text-gray-400 hover:text-white transition-colors"
            title="Toggle Controls Panel"
          >
            <Settings size={14} />
          </button>
        </div>
      </div>

      {/* Main Canvas Area */}
      <div className="flex-1 relative w-full h-full overflow-hidden bg-[#04080f]">
        
        {/* Render topology SVG */}
        <AdvancedTopologyVisualization
          graph={finalGraph}
          width={1200}
          height={800}
          blastRadiusNodes={blastRadiusNodes}
          rootCause={rootCauseNode || undefined}
          showPressure={true}
          showHealth={true}
          showEdgeWeights={true}
          animateUpdates={true}
          onNodeClick={handleNodeClick}
        />

        {/* Legend Overlay Panel (Bottom Left) */}
        <div className="absolute bottom-4 left-4 z-10 glass-panel p-3.5 rounded-xl border border-sentinel-700/40 max-w-[240px] space-y-2 pointer-events-none select-none">
          <div className="text-[9px] font-mono text-sentinel-accent/80 uppercase tracking-widest font-bold">Node Legend</div>
          <div className="space-y-1.5 text-[9px] font-mono text-gray-400">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400/25 border border-cyan-400" />
              <span>Healthy Cluster Nodes</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500/25 border border-amber-500" />
              <span>Degraded (In Blast Radius)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-red-600/25 border border-red-500 animate-pulse" />
              <span>Critical Failure Root Cause</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="border-t border-dashed border-red-400 w-4 h-0" />
              <span>Cascade Blast Propagation</span>
            </div>
          </div>
        </div>

        {/* Dynamic Controls Overlay Panel */}
        <AnimatePresence>
          {showControls && (
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -30 }}
              className="absolute top-4 left-4 z-20 glass-panel rounded-xl p-4 border border-sentinel-accent/30 w-72 space-y-4"
            >
              <div className="flex items-center justify-between border-b border-sentinel-700/30 pb-2">
                <span className="text-[10px] font-mono font-bold text-sentinel-accent uppercase tracking-wider">
                  Topology Controls
                </span>
                <button onClick={() => setShowControls(false)} className="text-gray-500 hover:text-white">
                  <X size={14} />
                </button>
              </div>

              <div className="space-y-2.5 text-[10px] font-mono text-gray-400">
                <div className="flex justify-between">
                  <span>Network Latency Avg</span>
                  <span className="text-green-400 font-bold">14 ms</span>
                </div>
                <div className="flex justify-between">
                  <span>Connection Stability</span>
                  <span className="text-cyan-400 font-bold">99.98%</span>
                </div>
                <div className="flex justify-between">
                  <span>Active Graph Nodes</span>
                  <span className="text-white font-bold">{finalGraph.node_count}</span>
                </div>
                <div className="flex justify-between">
                  <span>Graph Edge Count</span>
                  <span className="text-white font-bold">{finalGraph.edge_count}</span>
                </div>
              </div>

              <div className="space-y-2 border-t border-sentinel-700/30 pt-3">
                <span className="text-[8px] text-gray-500 uppercase tracking-widest font-bold">Diagnostics</span>
                <div className="text-[9px] text-gray-400 leading-relaxed font-mono">
                  All metrics are synced with Platform State Context. Hover nodes for instant stats. Click nodes to open cluster control actions.
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Cinematic Modal Overlay (Phase 4) */}
      <AnimatePresence>
        {selectedNode && (
          <div className="absolute inset-0 z-30 bg-black/60 backdrop-blur-sm flex items-center justify-center p-6">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="glass-panel w-full max-w-4xl border border-sentinel-accent/40 rounded-2xl overflow-hidden shadow-[0_0_50px_rgba(34,211,238,0.15)] flex flex-col md:flex-row h-[550px]"
            >
              
              {/* Left Side: General Info & Telemetry */}
              <div className="flex-1 p-6 border-b md:border-b-0 md:border-r border-sentinel-700/30 flex flex-col justify-between overflow-y-auto">
                <div className="space-y-6">
                  {/* Modal Header */}
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <Database size={16} className="text-sentinel-accent" />
                        <h2 className="text-lg font-display font-black text-white">{selectedNode.name}</h2>
                      </div>
                      <p className="text-[10px] font-mono text-gray-500 uppercase tracking-widest mt-1">
                        Type: {selectedNode.kind || "Deployment"} · ID: {selectedNode.id}
                      </p>
                    </div>

                    <span className={`text-[10px] font-mono uppercase px-2.5 py-1 rounded font-bold tracking-widest ${
                      selectedNode.health === "critical" ? "badge-critical animate-pulse" :
                      selectedNode.health === "degraded" ? "badge-high" : "badge-low"
                    }`}>
                      {selectedNode.health}
                    </span>
                  </div>

                  {/* Metrics Stats Grid */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="glass-panel-light p-3 rounded-xl border border-sentinel-700/30">
                      <div className="flex items-center justify-between text-[9px] font-mono text-gray-500 uppercase tracking-wider mb-1">
                        <span>CPU Loading</span>
                        <Cpu size={10} />
                      </div>
                      <div className="text-lg font-mono font-bold text-white">
                        {selectedNode.cpu_percent?.toFixed(1)}%
                      </div>
                    </div>

                    <div className="glass-panel-light p-3 rounded-xl border border-sentinel-700/30">
                      <div className="flex items-center justify-between text-[9px] font-mono text-gray-500 uppercase tracking-wider mb-1">
                        <span>Memory Alloc</span>
                        <TrendingUp size={10} />
                      </div>
                      <div className="text-lg font-mono font-bold text-white">
                        {selectedNode.memory_percent?.toFixed(1)}%
                      </div>
                    </div>

                    <div className="glass-panel-light p-3 rounded-xl border border-sentinel-700/30">
                      <div className="flex items-center justify-between text-[9px] font-mono text-gray-500 uppercase tracking-wider mb-1">
                        <span>Avg Latency</span>
                        <Activity size={10} />
                      </div>
                      <div className="text-lg font-mono font-bold text-cyan-400">
                        {selectedNode.health === "critical" ? "124.5 ms" : selectedNode.health === "degraded" ? "48.2 ms" : "2.8 ms"}
                      </div>
                    </div>

                    <div className="glass-panel-light p-3 rounded-xl border border-sentinel-700/30">
                      <div className="flex items-center justify-between text-[9px] font-mono text-gray-500 uppercase tracking-wider mb-1">
                        <span>Node Uptime</span>
                        <CheckCircle size={10} />
                      </div>
                      <div className="text-lg font-mono font-bold text-green-400">
                        {selectedNode.uptime_percent?.toFixed(2)}%
                      </div>
                    </div>
                  </div>

                  {/* Telemetry Chart */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono text-gray-500 uppercase tracking-widest">Live CPU Telemetry (1m)</span>
                      <span className="text-[9px] font-mono text-sentinel-accent">Live polling...</span>
                    </div>
                    <div className="h-16 bg-black/40 border border-sentinel-700/30 rounded-xl p-2 flex items-center justify-center overflow-hidden">
                      {localNodeMetrics[selectedNode.id] ? (
                        <svg className="w-full h-full" viewBox="0 0 240 40" preserveAspectRatio="none">
                          <path
                            d={getSparklinePath(localNodeMetrics[selectedNode.id].history)}
                            fill="none"
                            stroke="rgb(34, 211, 238)"
                            strokeWidth="1.5"
                            className="transition-all duration-300"
                          />
                        </svg>
                      ) : (
                        <span className="text-[9px] font-mono text-gray-600 uppercase">Awaiting buffer stream...</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Orchestration Control actions */}
                <div className="border-t border-sentinel-700/30 pt-4 mt-6">
                  <div className="flex items-center justify-between gap-3">
                    <button 
                      onClick={() => handleAction("RECYCLE_SERVICE")}
                      disabled={actionLoading !== null}
                      className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-sentinel-accent/15 border border-sentinel-accent/50 hover:bg-sentinel-accent/30 text-sentinel-accent rounded-xl text-xs font-mono font-bold transition-all disabled:opacity-50"
                    >
                      <RefreshCw size={12} className={actionLoading === "RECYCLE_SERVICE" ? "animate-spin" : ""} />
                      RECYCLE SERVICE
                    </button>
                    
                    <button 
                      onClick={() => handleAction("SCALE_REPLICAS")}
                      disabled={actionLoading !== null}
                      className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-yellow-500/15 border border-yellow-500/50 hover:bg-yellow-500/30 text-yellow-400 rounded-xl text-xs font-mono font-bold transition-all disabled:opacity-50"
                    >
                      <Zap size={12} className={actionLoading === "SCALE_REPLICAS" ? "animate-pulse" : ""} />
                      SCALE PODS
                    </button>
                  </div>
                </div>
              </div>

              {/* Right Side: AI Reasoning, Logs & Incident Forensics */}
              <div className="flex-1 p-6 bg-black/40 flex flex-col justify-between overflow-hidden">
                <div className="flex-1 flex flex-col space-y-4 min-h-0">
                  
                  {/* Close button */}
                  <div className="flex justify-end">
                    <button 
                      onClick={() => setSelectedNode(null)} 
                      className="p-1 hover:bg-white/5 border border-sentinel-700/40 rounded-lg text-gray-500 hover:text-white transition-all"
                    >
                      <X size={14} />
                    </button>
                  </div>

                  {/* AI Coprocessor Insight panel */}
                  <div className="glass-panel-light p-3.5 rounded-xl border border-purple-500/20 space-y-2">
                    <div className="flex items-center gap-1.5 text-[9px] font-mono text-purple-400 uppercase tracking-widest font-bold">
                      <Cpu size={12} />
                      <span>AI Coprocessor Diagnosis</span>
                    </div>
                    <p className="text-[11px] font-sans text-gray-300 leading-relaxed">
                      {selectedNode.health === "critical" ? (
                        "CRITICAL ANOMALY: Pod execution shows continuous heap growth. Socket pool exhausted. Remediation sequence is required to restore load-balancer SLA."
                      ) : selectedNode.health === "degraded" ? (
                        "WARNING: Service is experiencing cascading failure latency propagation from root cause node postgres-primary. Thread queue utilization stands at 82%."
                      ) : (
                        "Service performance metrics are within normal parameters. Network throughput matches baseline model forecasts with 98% confidence."
                      )}
                    </p>
                  </div>

                  {/* Incident History & System Logs list */}
                  <div className="flex-1 flex flex-col min-h-0 space-y-1.5">
                    <span className="text-[9px] font-mono text-gray-500 uppercase tracking-widest">Incidents & Audit Logs</span>
                    
                    <div className="flex-1 overflow-y-auto space-y-1.5 pr-1 font-mono text-[9px]">
                      {selectedNode.health === "critical" ? (
                        <>
                          <div className="p-2 border border-red-500/20 bg-red-950/20 text-red-400 rounded">
                            [15:08:44] [INC-0042] OOMKill threat escalation in progress.
                          </div>
                          <div className="p-2 border border-sentinel-700/40 bg-sentinel-950/40 text-gray-400 rounded">
                            [15:09:12] [SYS] Dispatching HeapProfiler agent probe.
                          </div>
                          <div className="p-2 border border-sentinel-700/40 bg-sentinel-950/40 text-gray-400 rounded">
                            [15:10:05] [SYS] Heap analysis: leaks detected in database connection pools.
                          </div>
                        </>
                      ) : selectedNode.health === "degraded" ? (
                        <>
                          <div className="p-2 border border-yellow-500/20 bg-yellow-950/20 text-yellow-400 rounded">
                            [15:09:05] [SYS] Connection pool exhaustion detected on postgres upstream.
                          </div>
                          <div className="p-2 border border-sentinel-700/40 bg-sentinel-950/40 text-gray-400 rounded">
                            [15:10:20] [SYS] Recycler target configured for auth-service pool.
                          </div>
                        </>
                      ) : (
                        <>
                          <div className="p-2 border border-green-500/20 bg-green-950/20 text-green-400 rounded">
                            [15:00:00] [SYS] Service successfully initialized.
                          </div>
                          <div className="p-2 border border-sentinel-700/40 bg-sentinel-950/40 text-gray-400 rounded">
                            [15:05:00] [SYS] Periodic baseline calibration succeeded.
                          </div>
                          <div className="p-2 border border-sentinel-700/40 bg-sentinel-950/40 text-gray-400 rounded">
                            [15:10:00] [SYS] Telemetry reports 0 anomalies in past 60m.
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                {/* Operation result messages */}
                <div className="h-10 mt-4 flex items-center justify-center">
                  <AnimatePresence mode="wait">
                    {actionLoading && (
                      <motion.div 
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        className="flex items-center gap-2 text-xs font-mono text-sentinel-accent animate-pulse"
                      >
                        <RefreshCw className="animate-spin w-3 h-3" />
                        Executing Cluster Orchestration Protocol...
                      </motion.div>
                    )}
                    {actionSuccess && (
                      <motion.div 
                        initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                        className="flex items-center gap-1.5 text-[10px] font-mono text-green-400 border border-green-500/30 bg-green-950/20 px-3 py-1.5 rounded-lg text-center"
                      >
                        <CheckCircle size={12} />
                        {actionSuccess}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>

            </motion.div>
          </div>
        )}
      </AnimatePresence>

    </div>
  );
}
