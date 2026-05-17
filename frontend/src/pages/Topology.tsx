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
    <div className="h-full flex flex-col relative">
      <header className="flex justify-between items-end mb-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-sentinel-accent/10 border border-sentinel-accent/30 rounded-lg flex items-center justify-center glow-border-accent">
            <Network size={24} className="text-sentinel-accent animate-pulse-slow" />
          </div>
          <div>
            <h1 className="text-3xl font-display font-bold text-white tracking-tight uppercase glow-text-accent">
              Neural Topology
            </h1>
            <p className="text-sm text-gray-400 font-sans tracking-widest uppercase mt-1">
              Live Infrastructure Graph
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4 glass-panel px-4 py-2 rounded-lg">
          <span className={`flex items-center gap-2 text-xs font-sans tracking-widest uppercase ${connected ? 'text-sentinel-success' : 'text-sentinel-danger'}`}>
            <span className={`inline-block w-2 h-2 rounded-full ${connected ? 'bg-sentinel-success shadow-[0_0_8px_#10b981] animate-pulse' : 'bg-sentinel-danger shadow-[0_0_8px_#ef4444]'}`} />
            {connected ? 'REALTIME SYNC' : 'OFFLINE'}
          </span>
        </div>
      </header>

      {/* KPI Overlays */}
      <div className="grid grid-cols-4 gap-4 mb-4">
        {[
          { label: "Active Nodes", value: topology?.node_count || 0, icon: <Cpu size={16} />, color: "text-sentinel-accent" },
          { label: "Neural Connections", value: topology?.edge_count || 0, icon: <Network size={16} />, color: "text-blue-400" },
          { label: "Blast Radius", value: cascadingNodes.size, icon: <ShieldAlert size={16} />, color: "text-red-400 glow-text-danger" },
          { label: "System Health", value: "99.9%", icon: <Activity size={16} />, color: "text-sentinel-success" },
        ].map((kpi, i) => (
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            key={i} 
            className="glass-panel p-3 rounded-xl flex items-center gap-4 border-l-4"
            style={{ borderLeftColor: 'var(--sentinel-accent)' }}
          >
            <div className={`p-2 rounded-lg bg-black/40 ${kpi.color}`}>{kpi.icon}</div>
            <div>
              <div className="text-[10px] text-gray-500 font-display uppercase tracking-widest">{kpi.label}</div>
              <div className={`text-xl font-bold font-sans ${kpi.color}`}>{kpi.value}</div>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="flex-1 relative rounded-xl overflow-hidden glass-panel border border-sentinel-700/50">
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="flex flex-col items-center gap-4">
               <div className="w-12 h-12 rounded-full border-t-2 border-r-2 border-sentinel-accent animate-spin" />
               <span className="text-sentinel-accent font-mono text-sm tracking-widest uppercase animate-pulse">Initializing D3 Physics Engine...</span>
            </div>
          </div>
        ) : topology && topology.nodes.length > 0 ? (
          <AdvancedTopologyVisualization
            graph={topology}
            blastRadiusNodes={blastRadiusArray}
            rootCause={rootCauseNode || undefined}
            showPressure={true}
            showHealth={true}
            showEdgeWeights={true}
            animateUpdates={true}
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-gray-500 font-mono text-sm">
            No topology data available.
          </div>
        )}
      </div>
    </div>
  );
}
