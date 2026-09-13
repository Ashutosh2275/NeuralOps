import { useEffect, useState } from "react";
import { api, TopologyGraph, TopologyNode } from "../lib/api";
import LiveTopology from "../components/topology/LiveTopology";
import {
  Network,
  Activity,
  ShieldAlert,
  Server,
  RefreshCw,
  Search,
  Box,
  Layers,
  ArrowRight,
  GitGraph,
  LayoutGrid,
} from "lucide-react";

export default function Topology() {
  const [topology, setTopology] = useState<TopologyGraph | null>(null);
  const [selectedNode, setSelectedNode] = useState<TopologyNode | null>(null);
  const [search, setSearch] = useState("");
  const [kindFilter, setKindFilter] = useState("all");
  const [viewMode, setViewMode] = useState<"graph" | "matrix">("graph");
  const [loading, setLoading] = useState(true);

  const loadTopology = async () => {
    setLoading(true);
    try {
      const data = await api.topology();
      setTopology(data);
      if (data.nodes.length > 0 && !selectedNode) {
        setSelectedNode(data.nodes[0]);
      }
    } catch {
      // keep existing
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTopology();
  }, []);

  const nodes = topology?.nodes || [];
  const edges = topology?.edges || [];

  const isNodeFailing = (node: TopologyNode) => {
    return (
      node.health === "critical" ||
      node.health === "warning" ||
      node.id.includes("crashloop") ||
      node.id.includes("oom")
    );
  };

  const filteredNodes = nodes.filter((n) => {
    const matchKind = kindFilter === "all" || (n.kind || "").toLowerCase() === kindFilter.toLowerCase();
    const matchSearch =
      !search ||
      n.id.toLowerCase().includes(search.toLowerCase()) ||
      (n.name || "").toLowerCase().includes(search.toLowerCase());
    return matchKind && matchSearch;
  });

  const getConnectedEdges = (nodeId: string) => {
    return edges.filter((e) => e.source === nodeId || e.target === nodeId);
  };

  return (
    <div className="space-y-4 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-white/5">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Network className="w-5 h-5 text-cyan-400" />
            <span>Service Dependency Topology</span>
          </h1>
          <p className="text-xs text-gray-400 font-mono mt-0.5">
            Live Kubernetes Multi-Tier Architecture & Dependency Propagation &bull; Namespace: <span className="text-cyan-400">sentinelops-e2e</span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* View Mode Toggle */}
          <div className="flex items-center bg-slate-800/80 rounded border border-slate-700 p-0.5 text-xs font-mono">
            <button
              onClick={() => setViewMode("graph")}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded transition ${
                viewMode === "graph"
                  ? "bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/40"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              <GitGraph className="w-3.5 h-3.5" />
              <span>Interactive Graph</span>
            </button>
            <button
              onClick={() => setViewMode("matrix")}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded transition ${
                viewMode === "matrix"
                  ? "bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/40"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              <span>Resource Matrix</span>
            </button>
          </div>

          <button
            onClick={loadTopology}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono bg-slate-800 hover:bg-slate-700 text-gray-300 rounded border border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Filter and stats bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-lg bg-slate-900/80 border border-slate-800 text-xs font-mono">
        <div className="flex items-center gap-2 flex-1 min-w-[220px]">
          <Search className="w-4 h-4 text-gray-500 shrink-0" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search topology nodes by name or resource ID..."
            className="w-full bg-transparent text-gray-200 placeholder-gray-500 focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-3">
          <select
            value={kindFilter}
            onChange={(e) => setKindFilter(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-gray-300 rounded px-2.5 py-1 text-xs focus:outline-none"
          >
            <option value="all">Kind: All ({nodes.length})</option>
            <option value="pod">Pods ({nodes.filter((n) => n.kind === "Pod").length})</option>
            <option value="service">Services ({nodes.filter((n) => n.kind === "Service").length})</option>
            <option value="deployment">Deployments ({nodes.filter((n) => n.kind === "Deployment").length})</option>
          </select>

          <div className="text-gray-400">
            Edges: <span className="text-cyan-400 font-bold">{edges.length}</span>
          </div>
        </div>
      </div>

      {/* Main split: Topology View & Node Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 cols: Interactive Force Graph or Cards Matrix */}
        <div className="lg:col-span-2 space-y-3">
          {viewMode === "graph" ? (
            <div className="h-[520px] rounded-lg border border-slate-800 bg-slate-950 overflow-hidden relative">
              <LiveTopology
                graph={topology}
                selectedNode={selectedNode?.id}
                onNodeSelect={(nodeId) => {
                  const match = nodes.find((n) => n.id === nodeId);
                  if (match) setSelectedNode(match);
                }}
              />
              <div className="absolute bottom-3 left-3 bg-slate-900/80 border border-slate-800 rounded px-2.5 py-1 text-[10px] font-mono text-gray-400 flex items-center gap-3 pointer-events-none">
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-400"></span> Healthy</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-400"></span> Warning / Restarting</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-400"></span> Critical Anomaly</span>
                <span>&bull; Drag to rearrange &bull; Scroll to zoom</span>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 max-h-[520px] overflow-y-auto pr-1">
              {filteredNodes.map((node) => {
                const isSelected = selectedNode?.id === node.id;
                const failing = isNodeFailing(node);
                return (
                  <button
                    key={node.id}
                    onClick={() => setSelectedNode(node)}
                    className={`p-3 rounded-lg border text-left transition space-y-2 block ${
                      isSelected
                        ? "bg-cyan-500/10 border-cyan-500/50 shadow-sm"
                        : failing
                        ? "bg-red-500/[0.04] border-red-500/30 hover:border-red-500/50"
                        : "bg-slate-900/70 border-slate-800 hover:bg-slate-800/50"
                    }`}
                  >
                    <div className="flex items-center justify-between text-[10px] font-mono">
                      <span
                        className={`uppercase px-1.5 py-0.2 rounded font-bold border ${
                          node.kind === "Pod"
                            ? "bg-purple-500/15 border-purple-500/30 text-purple-300"
                            : node.kind === "Service"
                            ? "bg-cyan-500/15 border-cyan-500/30 text-cyan-300"
                            : "bg-blue-500/15 border-blue-500/30 text-blue-300"
                        }`}
                      >
                        {node.kind || "Pod"}
                      </span>
                      <span
                        className={`w-2 h-2 rounded-full ${
                          failing ? "bg-red-400" : "bg-emerald-400"
                        }`}
                      />
                    </div>

                    <div className="text-xs font-mono font-medium text-gray-200 truncate">
                      {node.name || node.id.split("/").pop()}
                    </div>

                    <div className="text-[10px] font-mono text-gray-500 truncate">
                      ns: {node.namespace || "sentinelops-e2e"}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Right 1 col: Node Inspector Drawer */}
        <div className="space-y-4">
          {selectedNode ? (
            <div className="p-4 rounded-lg bg-slate-900/90 border border-slate-800 space-y-4 text-xs font-mono">
              <div className="flex items-center justify-between pb-2 border-b border-white/5">
                <span className="text-[10px] uppercase text-gray-400 font-bold">Node Inspector</span>
                <span className="text-[10px] text-cyan-400 uppercase font-bold">{selectedNode.kind}</span>
              </div>

              <div className="space-y-1">
                <div className="text-gray-400 text-[10px]">RESOURCE ID</div>
                <div className="text-white font-bold break-all">{selectedNode.id}</div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] pt-2 border-t border-white/5">
                <div>
                  <span className="text-gray-500 block">Namespace</span>
                  <span className="text-gray-200">{selectedNode.namespace || "sentinelops-e2e"}</span>
                </div>
                <div>
                  <span className="text-gray-500 block">Health Status</span>
                  <span
                    className={`font-bold ${
                      isNodeFailing(selectedNode) ? "text-red-400" : "text-emerald-400"
                    }`}
                  >
                    {isNodeFailing(selectedNode) ? "CRITICAL (ANOMALY)" : "HEALTHY"}
                  </span>
                </div>
              </div>

              {/* Connected Edges */}
              <div className="space-y-2 pt-2 border-t border-white/5">
                <span className="text-gray-400 text-[10px] font-bold uppercase">
                  Connected Dependencies ({getConnectedEdges(selectedNode.id).length})
                </span>
                <div className="space-y-1.5 max-h-60 overflow-y-auto">
                  {getConnectedEdges(selectedNode.id).length === 0 ? (
                    <div className="text-gray-500 text-[10px]">No direct route edges registered.</div>
                  ) : (
                    getConnectedEdges(selectedNode.id).map((e, idx) => (
                      <div
                        key={idx}
                        className="p-2 rounded bg-slate-800/60 border border-slate-700/60 flex items-center justify-between text-[11px]"
                      >
                        <span className="text-gray-300 truncate max-w-[110px]" title={e.source}>
                          {e.source.split("/").pop()}
                        </span>
                        <div className="flex flex-col items-center px-1">
                          <span className="text-[8px] text-gray-500 uppercase">{e.edge_type || "rel"}</span>
                          <ArrowRight className="w-3 h-3 text-cyan-400 shrink-0" />
                        </div>
                        <span className="text-cyan-300 truncate max-w-[110px]" title={e.target}>
                          {e.target.split("/").pop()}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-gray-500 text-xs font-mono bg-slate-900/60 rounded-lg border border-slate-800">
              Select a node in the graph or matrix to inspect dependency relationships.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
