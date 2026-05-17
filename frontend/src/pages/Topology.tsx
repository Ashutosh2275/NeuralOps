import { useEffect, useState } from "react";
import LiveTopology from "../components/topology/LiveTopology";
import AdvancedTopologyVisualization from "../components/topology/AdvancedTopologyVisualization";
import CascadingFailureVisualizer from "../components/topology/CascadingFailureVisualizer";
import { api, TopologyGraph, CascadingFailure } from "../lib/api";
import { useWebSocket } from "../hooks/useWebSocket";

export default function Topology() {
  const [topology, setTopology] = useState<TopologyGraph | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [cascadingFailure, setCascadingFailure] = useState<CascadingFailure | null>(null);
  const [cascadingNodes, setCascadingNodes] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [showAdvancedView, setShowAdvancedView] = useState(false);
  const [showPressure, setShowPressure] = useState(true);
  const [showHealth, setShowHealth] = useState(true);
  const [showEdgeWeights, setShowEdgeWeights] = useState(true);
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

  useEffect(() => {
    if (!selectedNode) return;

    const [namespace, kind, pod] = selectedNode.split("/");
    if (kind === "Pod" && pod) {
      api
        .cascadingFailure(namespace, pod)
        .then(setCascadingFailure)
        .catch(() => setCascadingFailure(null));
    }
  }, [selectedNode]);

  const blastRadiusArray = Array.from(cascadingNodes);

  return (
    <div className="space-y-6">
      <header className="flex justify-between items-center">
        <div>
          <h2 className="font-display text-2xl font-bold">Topology Intelligence</h2>
          <p className="text-gray-500 text-sm">Live dependency graph · Cascading failures · Health propagation</p>
        </div>
        <span className={`text-xs px-2 py-1 rounded ${connected ? "bg-green-900 text-green-300" : "bg-red-900"}`}>
          {connected ? "Live" : "Offline"}
        </span>
      </header>

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4">
          <p className="text-xs text-gray-500">Topology Nodes</p>
          <p className="text-3xl font-bold mt-1">{topology?.node_count ?? 0}</p>
        </div>
        <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4">
          <p className="text-xs text-gray-500">Dependencies</p>
          <p className="text-3xl font-bold mt-1">{topology?.edge_count ?? 0}</p>
        </div>
        <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4">
          <p className="text-xs text-gray-500">Cascading Events</p>
          <p className="text-3xl font-bold mt-1 text-red-400">{cascadingNodes.size}</p>
        </div>
      </div>

      {/* Visualization Controls */}
      {!loading && topology && topology.nodes.length > 0 && (
        <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4">
          <div className="flex gap-4 items-center flex-wrap">
            <button
              onClick={() => setShowAdvancedView(!showAdvancedView)}
              className={`px-4 py-2 rounded text-sm transition-colors ${
                showAdvancedView
                  ? "bg-blue-600 text-white"
                  : "bg-sentinel-700 text-gray-400 hover:bg-sentinel-600"
              }`}
            >
              {showAdvancedView ? "📊 Advanced View" : "📈 Standard View"}
            </button>

            {showAdvancedView && (
              <>
                <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer hover:text-white">
                  <input
                    type="checkbox"
                    checked={showPressure}
                    onChange={(e) => setShowPressure(e.target.checked)}
                    className="cursor-pointer"
                  />
                  Resource Pressure
                </label>
                <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer hover:text-white">
                  <input
                    type="checkbox"
                    checked={showHealth}
                    onChange={(e) => setShowHealth(e.target.checked)}
                    className="cursor-pointer"
                  />
                  Health Indicators
                </label>
                <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer hover:text-white">
                  <input
                    type="checkbox"
                    checked={showEdgeWeights}
                    onChange={(e) => setShowEdgeWeights(e.target.checked)}
                    className="cursor-pointer"
                  />
                  Edge Weights
                </label>
              </>
            )}
          </div>
        </div>
      )}

      {/* Main Visualization */}
      {loading ? (
        <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-8 text-center text-gray-500">
          Loading topology...
        </div>
      ) : topology && topology.nodes.length > 0 ? (
        <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4">
          {showAdvancedView ? (
            <AdvancedTopologyVisualization
              graph={topology}
              width={1000}
              height={500}
              blastRadiusNodes={blastRadiusArray}
              rootCause={rootCauseNode || undefined}
              showPressure={showPressure}
              showHealth={showHealth}
              showEdgeWeights={showEdgeWeights}
              animateUpdates={true}
            />
          ) : (
            <LiveTopology
              graph={topology}
              cascadingFailures={cascadingNodes}
              selectedNode={selectedNode || undefined}
              onNodeSelect={setSelectedNode}
            />
          )}
        </div>
      ) : (
        <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-12 text-center text-gray-500">
          No topology data yet. Deploy the demo e-commerce stack and start collectors.
        </div>
      )}

      {cascadingFailure && cascadingFailure.cascade && (
        <CascadingFailureVisualizer
          chain={cascadingFailure.cascade.chain}
          affectedCount={cascadingFailure.cascade.affected_count}
          propagationDepth={cascadingFailure.cascade.propagation_depth}
          escalationFactor={cascadingFailure.cascade.escalation_factor}
        />
      )}

      {selectedNode && !cascadingFailure && (
        <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4 text-center text-gray-400">
          <p>No cascading failures detected from {selectedNode}</p>
        </div>
      )}
    </div>
  );
}

