import React, { useEffect, useRef, useState, memo } from "react";
import * as d3 from "d3";
import type { TopologyGraph } from "../../lib/api";
import { motion, AnimatePresence } from "framer-motion";
import { X, Cpu, HardDrive, Wifi, AlertTriangle, CheckCircle, ZoomIn, ZoomOut, Maximize2 } from "lucide-react";

interface TopoNode extends d3.SimulationNodeDatum {
  id: string;
  name: string;
  kind?: string;
  health?: "healthy" | "degraded" | "critical";
  cpu_percent?: number;
  memory_percent?: number;
  in_blast_radius?: boolean;
  is_root_cause?: boolean;
  uptime_percent?: number;
  incident_count?: number;
}

interface TopoLink extends d3.SimulationLinkDatum<TopoNode> {
  source: string | TopoNode;
  target: string | TopoNode;
  weight?: number;
  traffic_rate?: number;
  in_blast_radius?: boolean;
}

interface AdvancedTopologyProps {
  graph: TopologyGraph;
  width?: number;
  height?: number;
  blastRadiusNodes?: string[];
  rootCause?: string;
  showPressure?: boolean;
  showHealth?: boolean;
  showEdgeWeights?: boolean;
  animateUpdates?: boolean;
  onNodeClick?: (node: any) => void;
}

export const AdvancedTopologyVisualization: React.FC<AdvancedTopologyProps> = ({
  graph,
  width = 1000,
  height = 600,
  blastRadiusNodes = [],
  rootCause,
  showPressure = true,
  showHealth = true,
  animateUpdates = true,
  onNodeClick,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);
  
  // Keep track of D3 instances
  const simRef = useRef<d3.Simulation<TopoNode, TopoLink> | null>(null);
  const linkGRef = useRef<d3.Selection<SVGGElement, unknown, null, undefined> | null>(null);
  const nodeGRef = useRef<d3.Selection<SVGGElement, unknown, null, undefined> | null>(null);
  const pktGRef = useRef<d3.Selection<SVGGElement, unknown, null, undefined> | null>(null);
  
  const [hoveredNode, setHoveredNode] = useState<TopoNode | null>(null);
  const [nodeCount, setNodeCount] = useState(0);
  const [linkCount, setLinkCount] = useState(0);

  // Helper for colors
  const getNodeColor = (d: TopoNode) => {
    if (d.in_blast_radius) return { fill: "rgba(239,68,68,0.25)", stroke: "#ef4444" };
    if (d.is_root_cause)   return { fill: "rgba(239,68,68,0.35)", stroke: "#ef4444" };
    if (showHealth && d.health === "critical") return { fill: "rgba(239,68,68,0.2)",  stroke: "#ef4444" };
    if (showHealth && d.health === "degraded") return { fill: "rgba(245,158,11,0.2)", stroke: "#f59e0b" };
    if (showPressure) {
      const avg = ((d.cpu_percent ?? 0) + (d.memory_percent ?? 0)) / 2;
      if (avg > 80) return { fill: "rgba(239,68,68,0.18)",  stroke: "#ef4444" };
      if (avg > 55) return { fill: "rgba(245,158,11,0.18)", stroke: "#f59e0b" };
    }
    return { fill: "rgba(34,211,238,0.15)", stroke: "#22d3ee" };
  };

  // INITIALIZATION EFFECT - RUNS ONLY ONCE
  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    
    // Check if already initialized
    if (simRef.current) return;
    
    svg.selectAll("*").remove();

    const parent = containerRef.current;
    const W = parent?.clientWidth || width;
    const H = parent?.clientHeight || height;
    svg.attr("viewBox", `0 0 ${W} ${H}`).attr("width", "100%").attr("height", "100%");

    // Defs
    const defs = svg.append("defs");

    // Glows
    const makeGlow = (id: string, color: string, blur: number) => {
      const f = defs.append("filter").attr("id", id).attr("x", "-60%").attr("y", "-60%").attr("width", "220%").attr("height", "220%");
      f.append("feFlood").attr("flood-color", color).attr("flood-opacity", 0.9).attr("result", "color");
      f.append("feComposite").attr("in", "color").attr("in2", "SourceAlpha").attr("operator", "in").attr("result", "shadow");
      f.append("feGaussianBlur").attr("in", "shadow").attr("stdDeviation", blur).attr("result", "blur");
      const m = f.append("feMerge");
      m.append("feMergeNode").attr("in", "blur");
      m.append("feMergeNode").attr("in", "SourceGraphic");
    };
    makeGlow("g-cyan", "#22d3ee", 5);
    makeGlow("g-red", "#ef4444", 8);
    makeGlow("g-amber", "#f59e0b", 4);
    makeGlow("g-white", "#ffffff", 2);

    // Radial Gradients
    const radGrad = (id: string, c1: string, c2: string) => {
      const rg = defs.append("radialGradient").attr("id", id);
      rg.append("stop").attr("offset", "0%").attr("stop-color", c1).attr("stop-opacity", 0.9);
      rg.append("stop").attr("offset", "100%").attr("stop-color", c2).attr("stop-opacity", 0.1);
    };
    radGrad("rg-cyan", "#22d3ee", "#083344");
    radGrad("rg-red", "#ef4444", "#450a0a");
    radGrad("rg-amber", "#f59e0b", "#451a03");

    // Background
    svg.append("rect").attr("width", W).attr("height", H).attr("fill", "#04080f");
    const ptG = svg.append("g").attr("opacity", 0.18);
    for (let x = 20; x < W + 100; x += 40)
      for (let y = 20; y < H + 100; y += 40)
        ptG.append("circle").attr("cx", x).attr("cy", y).attr("r", 0.8).attr("fill", "#22d3ee");

    const g = svg.append("g").attr("class", "graph-container");
    
    // Semantic layers
    linkGRef.current = g.append("g").attr("class", "links");
    pktGRef.current = g.append("g").attr("class", "packets");
    nodeGRef.current = g.append("g").attr("class", "nodes");

    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.08, 6])
      .on("zoom", (e) => g.attr("transform", e.transform));
    svg.call(zoom);
    zoomRef.current = zoom;

    // Simulation Setup
    simRef.current = d3.forceSimulation<TopoNode>()
      .force("link", d3.forceLink<TopoNode, TopoLink>().id(d => d.id).distance(d => d.in_blast_radius ? 180 : 110))
      .force("charge", d3.forceManyBody<TopoNode>().strength(-600))
      .force("center", d3.forceCenter(W / 2, H / 2).strength(0.06))
      .force("collision", d3.forceCollide<TopoNode>().radius(45))
      .alphaDecay(0.015);

    // Initial cinematic zoom
    if (animateUpdates) {
      svg.call(zoom.transform, d3.zoomIdentity.translate(W / 2 * 0.5, H / 2 * 0.5).scale(0.5));
      svg.transition().duration(2000).ease(d3.easeCubicOut).call(zoom.transform, d3.zoomIdentity.scale(1));
    }

    // Unmount cleanup
    return () => {
      if (simRef.current) simRef.current.stop();
      simRef.current = null;
    };
  }, []); // Run ONCE


  // UPDATE EFFECT - RUNS WHEN DATA CHANGES
  useEffect(() => {
    if (!graph?.nodes?.length || !simRef.current || !nodeGRef.current || !linkGRef.current) return;

    // 1. Prepare mapped data
    const nodes: TopoNode[] = (graph.nodes as any[]).map((n) => ({
      id: String(n.id ?? n.name ?? ""),
      name: String(n.name ?? n.id ?? "").split("/").pop() ?? "",
      kind: n.kind,
      health: n.health ?? "healthy",
      cpu_percent: n.cpu_percent ?? 20 + Math.random() * 60,
      memory_percent: n.memory_percent ?? 20 + Math.random() * 60,
      in_blast_radius: blastRadiusNodes.includes(String(n.id ?? "")),
      is_root_cause: String(n.id ?? "") === rootCause,
      uptime_percent: n.uptime_percent ?? 99.5,
      incident_count: n.incident_count ?? 0,
    }));

    const links: TopoLink[] = ((graph.edges ?? []) as any[]).map((e) => ({
      source: String(e.source),
      target: String(e.target),
      weight: e.weight ?? 1,
      traffic_rate: e.traffic_rate ?? Math.random() * 1000,
      in_blast_radius: blastRadiusNodes.includes(String(e.source)) && blastRadiusNodes.includes(String(e.target)),
    }));

    setNodeCount(nodes.length);
    setLinkCount(links.length);

    // Filter to avoid resetting existing node positions
    const oldNodes = simRef.current.nodes();
    const nodeMap = new Map(oldNodes.map(n => [n.id, n]));
    
    nodes.forEach(n => {
      const old = nodeMap.get(n.id);
      if (old) {
        n.x = old.x;
        n.y = old.y;
        n.vx = old.vx;
        n.vy = old.vy;
      }
    });

    // Update Simulation Data
    simRef.current.nodes(nodes);
    const linkForce = simRef.current.force("link") as d3.ForceLink<TopoNode, TopoLink>;
    linkForce.links(links);
    
    // We will handle ticking/alpha at the end after tick handlers are bound!


    // ── Update Links ──
    const linkSel = linkGRef.current.selectAll<SVGPathElement, TopoLink>("path").data(links, d => `${(d.source as any).id || d.source}-${(d.target as any).id || d.target}`);
    
    const linkEnter = linkSel.enter().append("path")
      .attr("fill", "none")
      .attr("opacity", 0);
      
    const linkUpdate = linkEnter.merge(linkSel);
    
    linkUpdate.transition().duration(500)
      .attr("stroke", d => d.in_blast_radius ? "rgba(239,68,68,0.75)" : "rgba(34,211,238,0.22)")
      .attr("stroke-width", d => d.in_blast_radius ? 2 : 1)
      .attr("filter", d => d.in_blast_radius ? "url(#g-red)" : "url(#g-cyan)")
      .attr("stroke-dasharray", d => d.in_blast_radius ? "5 4" : "none")
      .attr("opacity", 1);
      
    linkSel.exit().remove();

    // ── Update Nodes ──
    const nodeSel = nodeGRef.current.selectAll<SVGGElement, TopoNode>("g.toponode").data(nodes, d => d.id);
    
    const nodeEnter = nodeSel.enter().append("g")
      .attr("class", "toponode")
      .attr("cursor", "pointer")
      .attr("opacity", 0)
      .call(d3.drag<SVGGElement, TopoNode>()
        .on("start", (e, d) => { if (!e.active) simRef.current!.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on("drag",  (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on("end",   (e, d) => { if (!e.active) simRef.current!.alphaTarget(0); d.fx = null; d.fy = null; })
      )
      .on("click", (e, d) => { if(onNodeClick) onNodeClick(d); });

    // Handle Hover Interactivity natively inside node selection
    nodeEnter.on("mouseenter", (_e, d) => {
      setHoveredNode(d);
      if (linkGRef.current) {
        linkGRef.current.selectAll("path").attr("stroke-opacity", (l: any) =>
          ((l.source as TopoNode).id === d.id || (l.target as TopoNode).id === d.id) ? 1 : 0.05
        );
      }
    }).on("mouseleave", () => {
      setHoveredNode(null);
      if (linkGRef.current) {
        linkGRef.current.selectAll("path").attr("stroke-opacity", 1);
      }
    });

    // Structure inner elements for Enter block
    // Blast radius wrapper
    const blastRing = nodeEnter.append("circle").attr("class", "blast-ring");
    // Outer orbit
    const orbitRing = nodeEnter.append("circle").attr("class", "orbit-ring");
    // Main fill
    const mainCircle = nodeEnter.append("circle").attr("class", "main-circle");
    // Center dot
    const centerDot = nodeEnter.append("circle").attr("class", "center-dot");
    // Label
    const textLabel = nodeEnter.append("text").attr("class", "node-label");

    // Static Setup for orbit
    orbitRing.attr("r", 20).attr("fill", "none").attr("stroke-width", 0.5).attr("stroke-dasharray", "3 5")
      .append("animateTransform").attr("attributeName", "transform").attr("type", "rotate")
      .attr("from", "0").attr("to", "360").attr("dur", "20s").attr("repeatCount", "indefinite");

    textLabel.attr("text-anchor", "middle").style("pointer-events", "none").style("user-select", "none")
      .attr("font-family", "JetBrains Mono, monospace");

    // Merge and Update dynamic attributes
    const nodeUpdate = nodeEnter.merge(nodeSel);
    
    // Fast update opacity
    nodeUpdate.transition().duration(500).attr("opacity", 1);

    // Dynamic Blast Ring
    nodeUpdate.select(".blast-ring").transition().duration(300)
      .attr("r", 44)
      .attr("fill", "none")
      .attr("stroke", d => d.is_root_cause ? "rgba(239,68,68,0.35)" : (d.in_blast_radius ? "rgba(239,68,68,0.2)" : "rgba(0,0,0,0)"))
      .attr("stroke-width", 1);

    // Dynamic Orbit
    nodeUpdate.select(".orbit-ring").transition().duration(300)
      .attr("stroke", d => getNodeColor(d).stroke.replace(")", ",0.3)").replace("rgb", "rgba"));

    // Dynamic Main Circle
    nodeUpdate.select(".main-circle").transition().duration(300)
      .attr("r", d => d.is_root_cause ? 18 : 12)
      .attr("fill", d => {
        if (d.in_blast_radius || d.is_root_cause) return "url(#rg-red)";
        const avg = ((d.cpu_percent ?? 0) + (d.memory_percent ?? 0)) / 2;
        if (showPressure && avg > 80) return "url(#rg-red)";
        if (showPressure && avg > 55) return "url(#rg-amber)";
        if (showHealth && d.health === "critical") return "url(#rg-red)";
        if (showHealth && d.health === "degraded") return "url(#rg-amber)";
        return "url(#rg-cyan)";
      })
      .attr("stroke", d => getNodeColor(d).stroke)
      .attr("stroke-width", d => d.is_root_cause ? 2 : 1.5)
      .attr("filter", d => {
        if (d.in_blast_radius || d.is_root_cause) return "url(#g-red)";
        if (showHealth && d.health === "degraded") return "url(#g-amber)";
        return "url(#g-cyan)";
      });
      
    // Dynamic Center Dot
    nodeUpdate.select(".center-dot").transition().duration(300)
      .attr("r", d => d.is_root_cause ? 5 : 3)
      .attr("fill", d => (d.in_blast_radius || d.is_root_cause) ? "#ef4444" : (showHealth && d.health === "degraded" ? "#f59e0b" : "#22d3ee"))
      .attr("filter", "url(#g-white)");

    // Label Update
    nodeUpdate.select(".node-label")
      .text(d => d.name)
      .attr("dy", d => d.is_root_cause ? 34 : 26)
      .attr("fill", d => d.in_blast_radius ? "#fca5a5" : (d.is_root_cause ? "#fca5a5" : "#94a3b8"))
      .attr("font-size", d => d.is_root_cause ? "10px" : "8px")
      .attr("font-weight", d => d.is_root_cause ? "600" : "400");
      
    nodeSel.exit().transition().duration(500).attr("opacity", 0).remove();

    // Simulation Tick Update
    simRef.current.on("tick", () => {
      // Update link curves
      const p = linkGRef.current?.selectAll<SVGPathElement, TopoLink>("path");
      if (p) {
        p.attr("d", d => {
          const sx = (d.source as TopoNode).x ?? 0, sy = (d.source as TopoNode).y ?? 0;
          const tx = (d.target as TopoNode).x ?? 0, ty = (d.target as TopoNode).y ?? 0;
          const dx = tx - sx, dy = ty - sy;
          const len = Math.sqrt(dx*dx + dy*dy) || 1;
          const curve = Math.min(len * 0.35, 80);
          const mx = (sx + tx) / 2 - (dy / len) * curve;
          const my = (sy + ty) / 2 + (dx / len) * curve;
          return `M${sx},${sy} Q${mx},${my} ${tx},${ty}`;
        });
      }
      
      // Update node translations
      const n = nodeGRef.current?.selectAll<SVGGElement, TopoNode>("g.toponode");
      if (n) {
        n.attr("transform", d => `translate(${d.x ?? 0},${d.y ?? 0})`);
      }
    });

    // APPLY PHYSICS FIXES
    if (oldNodes.length === 0) {
      simRef.current.stop();
      for (let i = 0; i < 300; ++i) simRef.current.tick(); // Distribute nodes
    } else {
      simRef.current.alpha(0.01).restart();
      setTimeout(() => { if (simRef.current) simRef.current.stop(); }, 800);
    }

  }, [graph, blastRadiusNodes, rootCause, showPressure, showHealth, onNodeClick]);


  // ZOOM HANDLERS
  const handleZoom = (factor: number) => {
    if (!svgRef.current || !zoomRef.current) return;
    d3.select(svgRef.current).transition().duration(400).call(zoomRef.current.scaleBy, factor);
  };

  return (
    <div ref={containerRef} className="relative w-full h-full overflow-hidden" style={{ background: "#04080f", borderRadius: "inherit" }}>
      <svg ref={svgRef} className="w-full h-full" />

      {/* Overlays */}
      <div className="absolute top-4 right-4 z-10 flex flex-col gap-2">
        <button onClick={() => handleZoom(1.4)} className="glass-panel w-8 h-8 rounded-lg border border-sentinel-700/40 flex items-center justify-center text-gray-400 hover:text-sentinel-accent transition-all">
          <ZoomIn className="w-3.5 h-3.5" />
        </button>
        <button onClick={() => handleZoom(0.7)} className="glass-panel w-8 h-8 rounded-lg border border-sentinel-700/40 flex items-center justify-center text-gray-400 hover:text-sentinel-accent transition-all">
          <ZoomOut className="w-3.5 h-3.5" />
        </button>
      </div>

      {hoveredNode && (
        <AnimatePresence>
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 5 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 5 }}
            className="absolute bottom-4 left-4 z-20 glass-panel rounded-xl border border-sentinel-accent/40 p-4 w-72 shadow-neon-cyan"
            style={{ pointerEvents: "none" }}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="text-sm font-display font-bold text-white">{hoveredNode.name}</h3>
                <p className="text-[9px] font-mono text-sentinel-accent/50 uppercase tracking-widest">{hoveredNode.kind} · {hoveredNode.id.substring(0,8)}</p>
              </div>
              <span className={`text-[9px] px-1.5 py-0.5 rounded font-mono uppercase tracking-widest ${hoveredNode.health === "critical" ? "badge-critical" : hoveredNode.health === "degraded" ? "badge-high" : "badge-low"}`}>
                {hoveredNode.health}
              </span>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs font-mono">
                <Cpu className="text-gray-500 w-3 h-3"/><span className="text-gray-500 w-8">CPU</span>
                <div className="flex-1 h-1.5 bg-sentinel-900 rounded-full overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${hoveredNode.cpu_percent}%`, background: (hoveredNode.cpu_percent??0)>80?"#ef4444":"#22d3ee" }} />
                </div>
                <span className="text-sentinel-accent text-[10px] w-9 tabular-nums">{(hoveredNode.cpu_percent??0).toFixed(1)}%</span>
              </div>
              <div className="flex items-center gap-2 text-xs font-mono">
                <HardDrive className="text-gray-500 w-3 h-3"/><span className="text-gray-500 w-8">MEM</span>
                <div className="flex-1 h-1.5 bg-sentinel-900 rounded-full overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${hoveredNode.memory_percent}%`, background: (hoveredNode.memory_percent??0)>80?"#ef4444":"#22d3ee" }} />
                </div>
                <span className="text-sentinel-accent text-[10px] w-9 tabular-nums">{(hoveredNode.memory_percent??0).toFixed(1)}%</span>
              </div>
            </div>
            {hoveredNode.in_blast_radius && (
              <div className="mt-3 flex items-center gap-2 px-2 py-1.5 rounded-lg bg-red-500/15 border border-red-500/30">
                <AlertTriangle className="w-3 h-3 text-red-400" />
                <span className="text-[9px] font-mono text-red-400 uppercase tracking-widest">In Blast Radius</span>
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      )}
    </div>
  );
};
export default memo(AdvancedTopologyVisualization); // Add memo to prevent useless React rerenders
