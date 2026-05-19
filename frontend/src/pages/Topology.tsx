import { useEffect, useState } from "react";
import AdvancedTopologyVisualization from "../components/topology/AdvancedTopologyVisualization";
import { api, TopologyGraph } from "../lib/api";
import { useWebSocket } from "../hooks/useWebSocket";
import { Network, Activity, ShieldAlert, Cpu } from "lucide-react";
import { motion } from "framer-motion";

export default function Topology() {
  const [topology, setTopology] = useState<TopologyGraph | null>(null);
  const [cascadingNodes, setCascadingNodes] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [rootCauseNode, setRootCauseNode] = useState<string | null>(null);
  const [showHeader, setShowHeader] = useState(true);

  const { connected } = useWebSocket((e) => {
    if (e.type === "topology") {
      setTopology(e.payload as unknown as TopologyGraph);
    }
    if (e.type === "cascading_failure") {
      const cascade = e.payload as any;
      const affectedNodeIds = new Set<string>();
      cascade.chain?.forEach((item: any) => {
        affectedNodeIds.add(item.service);
        if (!rootCauseNode && item.root_cause) {
          setRootCauseNode(item.service);
        }
      });
      setCascadingNodes(affectedNodeIds);
    }
  });

  useEffect(() => {
    api
      .topology()
      .then(setTopology)
      .catch(() => setTopology({ nodes: [], edges: [], node_count: 0, edge_count: 0 }))
      .finally(() => setLoading(false));
  }, []);

  const blastRadiusArray = Array.from(cascadingNodes);

  return (
    <div className="h-full flex flex-col relative bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Compact Header - Collapsible */}
      {showHeader && (
        <motion.header
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="flex justify-between items-center px-6 py-3 border-b border-sentinel-accent/20 bg-gradient-to-r from-black/40 to-transparent"
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-sentinel-accent/10 border border-sentinel-accent/30 rounded-lg flex items-center justify-center glow-border-accent">
              <Network size={18} className="text-sentinel-accent animate-pulse-slow" />
            </div>
            <div>
              <h1 className="text-xl font-display font-bold text-white tracking-tight uppercase glow-text-accent">
                Neural Canvas
              </h1>
              <p className="text-xs text-gray-500 font-mono tracking-widest">
                {topology?.node_count || 0} Nodes · {topology?.edge_count || 0} Edges
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className={`flex items-center gap-2 text-[10px] font-sans tracking-widest uppercase px-3 py-1 rounded-full ${connected ? 'bg-sentinel-success/20 text-sentinel-success' : 'bg-sentinel-danger/20 text-sentinel-danger'}`}>
              <span className={`inline-block w-2 h-2 rounded-full ${connected ? 'bg-sentinel-success shadow-[0_0_8px_#10b981] animate-pulse' : 'bg-sentinel-danger'}`} />
              {connected ? 'LIVE' : 'OFFLINE'}
            </span>
            <button
              onClick={() => setShowHeader(false)}
              className="p-1 hover:bg-white/10 rounded-lg transition-colors text-gray-400 hover:text-white"
              title="Collapse header to maximize map"
            >
              ✕
            </button>
          </div>
        </motion.header>
      )}

      {/* Collapsed Header Toggle */}
      {!showHeader && (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          onClick={() => setShowHeader(true)}
          className="absolute top-4 left-4 z-10 px-2 py-1 text-[10px] font-mono bg-sentinel-accent/20 border border-sentinel-accent/50 rounded text-sentinel-accent hover:bg-sentinel-accent/30 transition-colors"
          title="Show header"
        >
          ≡ NEURAL CANVAS
        </motion.button>
      )}

      {/* Compact KPI Overlay - Fixed at top-right */}
      <div className="absolute top-4 right-4 z-20 flex flex-col gap-2 pointer-events-none">
        {[
          { label: "Nodes", value: topology?.node_count || 0, color: "text-cyan-400" },
          { label: "Edges", value: topology?.edge_count || 0, color: "text-blue-400" },
          { label: "Blast", value: cascadingNodes.size, color: "text-red-400" },
          { label: "Health", value: "99.9%", color: "text-green-400" },
        ].map((kpi, i) => (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            key={i}
            className="glass-panel px-3 py-1 rounded-lg text-right pointer-events-auto"
          >
            <div className="text-[9px] text-gray-500 font-mono uppercase tracking-widest">{kpi.label}</div>
            <div className={`text-sm font-bold font-sans ${kpi.color}`}>{kpi.value}</div>
          </motion.div>
        ))}
      </div>

      {/* Full-Width Topology Map */}
      <div className="flex-1 relative w-full overflow-hidden">
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-b from-transparent to-black/20">
            <div className="flex flex-col items-center gap-4">
              <div className="w-16 h-16 rounded-full border-t-2 border-r-2 border-sentinel-accent animate-spin" />
              <span className="text-sentinel-accent font-mono text-sm tracking-widest uppercase animate-pulse">
                Rendering Neural Map...
              </span>
            </div>
          </div>
        ) : topology && topology.nodes.length > 0 ? (
          <div className="w-full h-full">
            <AdvancedTopologyVisualization
              graph={topology}
              width={typeof window !== 'undefined' ? window.innerWidth : 1920}
              height={typeof window !== 'undefined' ? window.innerHeight - (showHeader ? 120 : 60) : 1080}
              blastRadiusNodes={blastRadiusArray}
              rootCause={rootCauseNode || undefined}
              showPressure={true}
              showHealth={true}
              showEdgeWeights={true}
              animateUpdates={true}
            />
          </div>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-gray-600 font-mono text-sm bg-gradient-to-b from-transparent to-black/40">
            <div className="text-center">
              <div className="text-2xl mb-2">⚛️</div>
              <div>No topology data. Deploy infrastructure to visualize.</div>
            </div>
          </div>
        )}
      </div>

      {/* Legend - Fixed at bottom-left */}
      <div className="absolute bottom-4 left-4 z-20 glass-panel px-4 py-3 rounded-lg border border-sentinel-accent/30 max-w-xs">
        <div className="text-[10px] font-mono text-sentinel-accent uppercase tracking-widest font-bold mb-2">Legend</div>
        <div className="space-y-1 text-[9px] text-gray-400">
          <div>🔴 Red: Critical · 🟠 Orange: Degraded · 🟢 Green: Healthy</div>
          <div>💥 Dashed Circle: Blast Radius</div>
          <div>→ Line Thickness: Traffic Rate</div>
        </div>
      </div>
    </div>
  );
}

