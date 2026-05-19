import { useEffect, useState } from "react";
import AdvancedTopologyVisualization from "../components/topology/AdvancedTopologyVisualization";
import { api, TopologyGraph } from "../lib/api";
import { useWebSocket } from "../hooks/useWebSocket";
import { Network, Activity, ShieldAlert, Cpu, X, Menu } from "lucide-react";
import { motion } from "framer-motion";

export default function Topology() {
  const [topology, setTopology] = useState<TopologyGraph | null>(null);
  const [cascadingNodes, setCascadingNodes] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [rootCauseNode, setRootCauseNode] = useState<string | null>(null);
  const [showControls, setShowControls] = useState(false);

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
    <div className="fixed inset-0 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex flex-col overflow-hidden">
      {/* Minimalist Top Bar */}
      <motion.div
        className="h-12 bg-black/40 border-b border-sentinel-accent/20 flex items-center justify-between px-4 flex-shrink-0"
        initial={{ y: -50 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-sentinel-accent/20 border border-sentinel-accent/50 rounded flex items-center justify-center">
            <Network size={14} className="text-sentinel-accent" />
          </div>
          <span className="text-xs font-mono text-sentinel-accent uppercase tracking-widest">Neural Canvas</span>
        </div>

        <div className="flex items-center gap-3">
          {/* Live Status */}
          <span className={`flex items-center gap-1.5 text-[10px] font-mono uppercase px-2 py-1 rounded ${connected ? 'text-green-400 bg-green-500/20' : 'text-red-400 bg-red-500/20'}`}>
            <span className={`inline-block w-1.5 h-1.5 rounded-full ${connected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
            {connected ? 'LIVE' : 'OFFLINE'}
          </span>

          {/* Stats */}
          <div className="hidden sm:flex items-center gap-3 border-l border-sentinel-accent/20 pl-3 text-[10px] font-mono text-gray-400">
            <div><span className="text-cyan-400">{topology?.node_count || 0}</span> nodes</div>
            <div>·</div>
            <div><span className="text-blue-400">{topology?.edge_count || 0}</span> edges</div>
            {cascadingNodes.size > 0 && (
              <>
                <div>·</div>
                <div><span className="text-red-400">{cascadingNodes.size}</span> blast</div>
              </>
            )}
          </div>

          {/* Controls Toggle */}
          <button
            onClick={() => setShowControls(!showControls)}
            className="p-1.5 hover:bg-white/10 rounded transition-colors text-gray-400 hover:text-white"
            title="Toggle controls"
          >
            {showControls ? <X size={16} /> : <Menu size={16} />}
          </button>
        </div>
      </motion.div>

      {/* Main Canvas Container - Full Remaining Space */}
      <div className="flex-1 relative w-full overflow-hidden">
        {/* Loading State */}
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-b from-transparent to-black/20 z-10">
            <div className="flex flex-col items-center gap-3">
              <div className="w-12 h-12 rounded-full border-t-2 border-r-2 border-sentinel-accent animate-spin" />
              <span className="text-sentinel-accent font-mono text-xs tracking-widest uppercase animate-pulse">
                Initializing Neural Engine...
              </span>
            </div>
          </div>
        )}

        {/* Topology Visualization - Full Canvas */}
        {topology && topology.nodes.length > 0 ? (
          <div className="w-full h-full">
            <AdvancedTopologyVisualization
              graph={topology}
              width={typeof window !== 'undefined' ? window.innerWidth : 1920}
              height={typeof window !== 'undefined' ? window.innerHeight - 48 : 1080}
              blastRadiusNodes={blastRadiusArray}
              rootCause={rootCauseNode || undefined}
              showPressure={true}
              showHealth={true}
              showEdgeWeights={true}
              animateUpdates={true}
            />
          </div>
        ) : !loading ? (
          <div className="absolute inset-0 flex items-center justify-center text-gray-600 font-mono text-sm bg-gradient-to-b from-transparent to-black/40">
            <div className="text-center">
              <div className="text-3xl mb-2">⚛️</div>
              <div>No topology data</div>
              <div className="text-xs text-gray-500 mt-1">Deploy infrastructure to visualize</div>
            </div>
          </div>
        ) : null}

        {/* Floating Controls Panel */}
        {showControls && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="absolute top-4 left-4 z-20 glass-panel rounded-lg p-4 border border-sentinel-accent/30 max-w-sm space-y-3"
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-mono text-sentinel-accent uppercase tracking-widest font-bold">
                Neural Canvas Controls
              </h3>
              <button
                onClick={() => setShowControls(false)}
                className="p-1 hover:bg-white/10 rounded text-gray-400 hover:text-white"
              >
                <X size={14} />
              </button>
            </div>

            {/* Stats */}
            <div className="space-y-2 border-t border-sentinel-accent/20 pt-3">
              <div className="text-[10px] text-gray-400">
                <div className="flex justify-between mb-1">
                  <span>Active Nodes</span>
                  <span className="text-cyan-400 font-bold">{topology?.node_count || 0}</span>
                </div>
                <div className="flex justify-between mb-1">
                  <span>Neural Connections</span>
                  <span className="text-blue-400 font-bold">{topology?.edge_count || 0}</span>
                </div>
                <div className="flex justify-between mb-1">
                  <span>Blast Radius</span>
                  <span className="text-red-400 font-bold">{cascadingNodes.size}</span>
                </div>
                <div className="flex justify-between">
                  <span>System Health</span>
                  <span className="text-green-400 font-bold">99.9%</span>
                </div>
              </div>
            </div>

            {/* Legend */}
            <div className="border-t border-sentinel-accent/20 pt-3 space-y-1">
              <div className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-2">Legend</div>
              <div className="text-[9px] text-gray-400 space-y-1">
                <div>🔴 Red: Critical | 🟠 Degraded | 🟢 Healthy</div>
                <div>💥 Dashed: Blast Radius</div>
                <div>→ Thickness: Traffic Rate</div>
              </div>
            </div>

            {/* Interaction Help */}
            <div className="border-t border-sentinel-accent/20 pt-3 text-[9px] text-gray-500">
              <div className="font-bold text-gray-400 mb-1">Interactions</div>
              <div>🖱️ Hover for details</div>
              <div>🔍 Scroll to zoom</div>
              <div>🖱️ Drag to pan</div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}


