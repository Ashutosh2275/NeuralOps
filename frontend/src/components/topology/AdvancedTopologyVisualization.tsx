import React, { useEffect, useRef, useState } from "react";
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
}

function getNodeColor(d: TopoNode, showPressure: boolean, showHealth: boolean) {
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
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);
  const [hoveredNode, setHoveredNode] = useState<TopoNode | null>(null);
  const [nodeCount, setNodeCount] = useState(0);
  const [linkCount, setLinkCount] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    if (!svgRef.current || !graph?.nodes?.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const parent = containerRef.current;
    const W = parent?.clientWidth  || width;
    const H = parent?.clientHeight || height;
    svg.attr("viewBox", `0 0 ${W} ${H}`).attr("width", "100%").attr("height", "100%");

    // ── Node + Link data ────────────────────────────────────
    const nodes: TopoNode[] = (graph.nodes as any[]).map((n) => ({
      id:              String(n.id ?? n.name ?? ""),
      name:            String(n.name ?? n.id ?? "").split("/").pop() ?? "",
      kind:            n.kind,
      health:          n.health ?? "healthy",
      cpu_percent:     n.cpu_percent  ?? 20 + Math.random() * 60,
      memory_percent:  n.memory_percent ?? 20 + Math.random() * 60,
      in_blast_radius: blastRadiusNodes.includes(String(n.id ?? "")),
      is_root_cause:   String(n.id ?? "") === rootCause,
      uptime_percent:  n.uptime_percent ?? 99.5,
      incident_count:  n.incident_count ?? 0,
    }));

    const links: TopoLink[] = ((graph.edges ?? []) as any[]).map((e) => ({
      source:          String(e.source),
      target:          String(e.target),
      weight:          e.weight ?? 1,
      traffic_rate:    e.traffic_rate ?? Math.random() * 1000,
      in_blast_radius: blastRadiusNodes.includes(String(e.source)) &&
                       blastRadiusNodes.includes(String(e.target)),
    }));

    setNodeCount(nodes.length);
    setLinkCount(links.length);

    // ── SVG Defs ────────────────────────────────────────────
    const defs = svg.append("defs");

    // Glow filters
    const makeGlow = (id: string, color: string, blur = 5) => {
      const f = defs.append("filter").attr("id", id)
        .attr("x", "-60%").attr("y", "-60%").attr("width", "220%").attr("height", "220%");
      f.append("feFlood").attr("flood-color", color).attr("flood-opacity", 0.9).attr("result", "color");
      f.append("feComposite").attr("in", "color").attr("in2", "SourceAlpha").attr("operator", "in").attr("result", "shadow");
      f.append("feGaussianBlur").attr("in", "shadow").attr("stdDeviation", blur).attr("result", "blur");
      const m = f.append("feMerge");
      m.append("feMergeNode").attr("in", "blur");
      m.append("feMergeNode").attr("in", "SourceGraphic");
    };
    makeGlow("g-cyan",   "#22d3ee", 5);
    makeGlow("g-red",    "#ef4444", 8);
    makeGlow("g-amber",  "#f59e0b", 4);
    makeGlow("g-white",  "#ffffff", 2);
    makeGlow("g-green",  "#10b981", 4);

    // Radial gradient for nodes
    const radGrad = (id: string, c1: string, c2: string) => {
      const rg = defs.append("radialGradient").attr("id", id);
      rg.append("stop").attr("offset", "0%").attr("stop-color", c1).attr("stop-opacity", 0.9);
      rg.append("stop").attr("offset", "100%").attr("stop-color", c2).attr("stop-opacity", 0.1);
    };
    radGrad("rg-cyan",  "#22d3ee", "#083344");
    radGrad("rg-red",   "#ef4444", "#450a0a");
    radGrad("rg-amber", "#f59e0b", "#451a03");
    radGrad("rg-green", "#10b981", "#064e3b");

    // ── Background ──────────────────────────────────────────
    // Dark base
    svg.append("rect").attr("width", W).attr("height", H).attr("fill", "#04080f");
    // Subtle dot-grid
    const ptG = svg.append("g").attr("opacity", 0.18);
    for (let x = 20; x < W; x += 40)
      for (let y = 20; y < H; y += 40)
        ptG.append("circle").attr("cx", x).attr("cy", y).attr("r", 0.8).attr("fill", "#22d3ee");
    // Radial ambient from center
    defs.append("radialGradient").attr("id", "bg-ambient")
      .call(g => {
        g.append("stop").attr("offset", "0%").attr("stop-color", "#22d3ee").attr("stop-opacity", 0.05);
        g.append("stop").attr("offset", "100%").attr("stop-color", "transparent").attr("stop-opacity", 0);
      });
    svg.append("ellipse").attr("cx", W/2).attr("cy", H/2).attr("rx", W*0.6).attr("ry", H*0.5)
      .attr("fill", "url(#bg-ambient)");

    // ── Zoom ────────────────────────────────────────────────
    const g = svg.append("g");
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.08, 6])
      .on("zoom", (e) => g.attr("transform", e.transform));
    svg.call(zoom);
    zoomRef.current = zoom;

    // Cinematic zoom-in on load — start at 0.4 centered so nodes appear immediately
    if (animateUpdates) {
      const initScale = nodes.length > 100 ? 0.3 : 0.5;
      svg.call(zoom.transform, d3.zoomIdentity.translate(W / 2 * (1 - initScale), H / 2 * (1 - initScale)).scale(initScale));
      svg.transition().duration(2000).ease(d3.easeCubicOut)
        .call(zoom.transform, d3.zoomIdentity.scale(1));
    }

    // ── D3 Simulation ───────────────────────────────────────
    const sim = d3
      .forceSimulation<TopoNode>(nodes)
      .force("link",      d3.forceLink<TopoNode, TopoLink>(links).id(d => d.id).distance((d: any) => d.in_blast_radius ? 180 : 110))
      .force("charge",    d3.forceManyBody<TopoNode>().strength(-500))
      .force("center",    d3.forceCenter(W / 2, H / 2).strength(0.05))
      .force("collision", d3.forceCollide<TopoNode>().radius(42))
      .alphaDecay(0.02);

    // ── Link layer ──────────────────────────────────────────
    const linkG = g.append("g").attr("class", "links");
    const linkEls = linkG.selectAll<SVGPathElement, TopoLink>("path")
      .data(links).join("path")
      .attr("fill", "none")
      .attr("stroke", (d) => d.in_blast_radius ? "rgba(239,68,68,0.75)" : "rgba(34,211,238,0.22)")
      .attr("stroke-width", (d) => d.in_blast_radius ? 2 : 1)
      .attr("filter", (d) => d.in_blast_radius ? "url(#g-red)" : "url(#g-cyan)")
      .attr("stroke-dasharray", (d) => d.in_blast_radius ? "5 4" : "none")
      .attr("opacity", 0)
      .call(sel => sel.transition().duration(1200).delay((_,i) => i * 2).attr("opacity", 1));

    // Animated dashes for blast-radius links
    const animateDash = () => {
      let offset = 0;
      const t = d3.timer(() => {
        offset -= 0.5;
        linkEls.filter((d: any) => d.in_blast_radius)
          .attr("stroke-dashoffset", offset);
      });
      return t;
    };
    const dashTimer = animateDash();

    // ── Packet layer ─────────────────────────────────────────
    const pktG = g.append("g").attr("class", "packets");

    // ── Node layer ───────────────────────────────────────────
    const nodeG = g.append("g").attr("class", "nodes");
    const nodeEls = nodeG.selectAll<SVGGElement, TopoNode>("g")
      .data(nodes).join("g")
      .attr("cursor", "pointer")
      .attr("opacity", 0)
      .call(sel => sel.transition().duration(600).delay((_,i) => 400 + i * 3).attr("opacity", 1));

    // Drag
    nodeEls.call(
      d3.drag<SVGGElement, TopoNode>()
        .on("start", (e, d) => { if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on("drag",  (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on("end",   (e, d) => { if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; })
    );

    // Hover
    nodeEls
      .on("mouseenter", (_e, d) => {
        setHoveredNode(d);
        linkEls.attr("stroke-opacity", (l: any) =>
          (l.source as TopoNode).id === d.id || (l.target as TopoNode).id === d.id ? 1 : 0.05
        );
        d3.select(_e.currentTarget as SVGGElement)
          .selectAll("circle.main-circle")
          .transition().duration(200)
          .attr("r", (rd: any) => (d.is_root_cause ? 22 : 16));
      })
      .on("mouseleave", (_e) => {
        setHoveredNode(null);
        linkEls.attr("stroke-opacity", 1);
        d3.select(_e.currentTarget as SVGGElement)
          .selectAll("circle.main-circle")
          .transition().duration(200)
          .attr("r", (rd: any) => (rd.is_root_cause ? 18 : 12));
      });

    // ── Draw node elements ───────────────────────────────────

    // Outer pulse ring (blast radius)
    nodeEls.filter(d => !!d.in_blast_radius || !!d.is_root_cause)
      .append("circle")
      .attr("r", 44)
      .attr("fill", "none")
      .attr("stroke", d => d.is_root_cause ? "rgba(239,68,68,0.35)" : "rgba(239,68,68,0.2)")
      .attr("stroke-width", 1)
      .append("animate")
      .attr("attributeName", "r").attr("values", "28;52;28")
      .attr("dur", d => (d as any).is_root_cause ? "1.8s" : "2.5s")
      .attr("repeatCount", "indefinite")
      .attr("calcMode", "spline")
      .attr("keySplines", "0.4 0 0.6 1;0.4 0 0.6 1");

    // Inner orbit ring (all nodes)
    nodeEls.append("circle")
      .attr("r", 20)
      .attr("fill", "none")
      .attr("stroke", d => {
        const c = getNodeColor(d, showPressure, showHealth);
        return c.stroke.replace(")", "/0.3)").replace("rgb", "rgba");
      })
      .attr("stroke-width", 0.5)
      .attr("stroke-dasharray", "3 5")
      .append("animateTransform")
      .attr("attributeName", "transform").attr("type", "rotate")
      .attr("from", "0").attr("to", "360")
      .attr("dur", "20s").attr("repeatCount", "indefinite");

    // Main node circle (using radial gradient)
    nodeEls.append("circle")
      .attr("class", "main-circle")
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
      .attr("stroke", d => getNodeColor(d, showPressure, showHealth).stroke)
      .attr("stroke-width", d => d.is_root_cause ? 2 : 1.5)
      .attr("filter", d => {
        if (d.in_blast_radius || d.is_root_cause) return "url(#g-red)";
        if (showHealth && d.health === "degraded") return "url(#g-amber)";
        return "url(#g-cyan)";
      });

    // Bright center dot
    nodeEls.append("circle")
      .attr("r", d => d.is_root_cause ? 5 : 3)
      .attr("fill", d => {
        if (d.in_blast_radius || d.is_root_cause) return "#ef4444";
        if (showHealth && d.health === "degraded") return "#f59e0b";
        return "#22d3ee";
      })
      .attr("filter", "url(#g-white)");

    // Labels
    nodeEls.append("text")
      .text(d => d.name)
      .attr("dy", d => d.is_root_cause ? 34 : 26)
      .attr("text-anchor", "middle")
      .attr("fill", d => d.in_blast_radius ? "#fca5a5" : d.is_root_cause ? "#fca5a5" : "#94a3b8")
      .attr("font-family", "JetBrains Mono, monospace")
      .attr("font-size", d => d.is_root_cause ? "10px" : "8px")
      .attr("font-weight", d => d.is_root_cause ? "600" : "400")
      .style("pointer-events", "none")
      .style("user-select", "none");

    // ── Packet animation ─────────────────────────────────────
    let tick = 0;
    const pktTimer = d3.timer(() => {
      tick++;
      if (tick % 6 === 0 && links.length > 0) {
        const l = links[Math.floor(Math.random() * links.length)];
        const s = l.source as TopoNode;
        const t = l.target as TopoNode;
        if (!s.x || !t.x) return;
        const isBlast = l.in_blast_radius;
        pktG.append("circle")
          .attr("r", isBlast ? 3 : 2)
          .attr("fill", isBlast ? "#ef4444" : "#22d3ee")
          .attr("filter", isBlast ? "url(#g-red)" : "url(#g-cyan)")
          .attr("cx", s.x ?? 0).attr("cy", s.y ?? 0)
          .attr("opacity", 0.9)
          .transition().duration(isBlast ? 2000 : 1000).ease(d3.easeLinear)
          .attr("cx", t.x ?? 0).attr("cy", t.y ?? 0)
          .attr("opacity", 0)
          .remove();
      }
    });

    // ── Tick handler ─────────────────────────────────────────
    sim.on("tick", () => {
      linkEls.attr("d", (d: any) => {
        const sx = d.source.x ?? 0, sy = d.source.y ?? 0;
        const tx = d.target.x ?? 0, ty = d.target.y ?? 0;
        const dx = tx - sx, dy = ty - sy;
        const len = Math.sqrt(dx*dx + dy*dy) || 1;
        const curve = Math.min(len * 0.35, 80);
        const mx = (sx + tx) / 2 - (dy / len) * curve;
        const my = (sy + ty) / 2 + (dx / len) * curve;
        return `M${sx},${sy} Q${mx},${my} ${tx},${ty}`;
      });
      nodeEls.attr("transform", d => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    return () => {
      sim.stop();
      pktTimer.stop();
      dashTimer.stop();
    };
  }, [graph, blastRadiusNodes, rootCause, showPressure, showHealth]);

  const handleZoom = (factor: number) => {
    if (!svgRef.current || !zoomRef.current) return;
    d3.select(svgRef.current)
      .transition().duration(400)
      .call(zoomRef.current.scaleBy, factor);
  };

  return (
    <div ref={containerRef} className="relative w-full h-full overflow-hidden" style={{ background: "#04080f", borderRadius: "inherit" }}>
      <svg ref={svgRef} className="w-full h-full" />

      {/* Live badge */}
      <div className="absolute top-4 left-4 flex items-center gap-2 glass-panel px-3 py-1.5 rounded-lg border border-sentinel-accent/30 z-10">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sentinel-accent opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-sentinel-accent" />
        </span>
        <span className="text-[9px] font-mono text-sentinel-accent uppercase tracking-[0.2em]">Neural Canvas</span>
      </div>

      {/* Zoom controls */}
      <div className="absolute top-4 right-4 z-10 flex flex-col gap-2">
        <button onClick={() => handleZoom(1.4)}
          className="glass-panel w-8 h-8 rounded-lg border border-sentinel-700/40 flex items-center justify-center text-gray-400 hover:text-sentinel-accent hover:border-sentinel-accent/40 transition-all">
          <ZoomIn className="w-3.5 h-3.5" />
        </button>
        <button onClick={() => handleZoom(0.7)}
          className="glass-panel w-8 h-8 rounded-lg border border-sentinel-700/40 flex items-center justify-center text-gray-400 hover:text-sentinel-accent hover:border-sentinel-accent/40 transition-all">
          <ZoomOut className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Stats overlay */}
      <div className="absolute bottom-4 right-4 z-10 glass-panel px-3 py-2 rounded-lg border border-sentinel-700/40 text-right space-y-0.5">
        <div className="text-[9px] font-mono text-sentinel-accent/60 uppercase tracking-widest">{nodeCount} nodes · {linkCount} edges</div>
        <div className="text-[8px] font-mono text-gray-600 uppercase tracking-wider animate-pulse">Scroll→Zoom · Drag→Pan</div>
      </div>

      {/* Node tooltip */}
      <AnimatePresence>
        {hoveredNode && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 10 }}
            animate={{ opacity: 1, scale: 1,   y: 0 }}
            exit={{ opacity: 0,  scale: 0.9, y: 10 }}
            transition={{ duration: 0.18, ease: "easeOut" }}
            className="absolute bottom-4 left-4 z-20 glass-panel rounded-xl border border-sentinel-accent/40 p-4 w-72 shadow-neon-cyan"
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="text-sm font-display font-bold text-white leading-none">{hoveredNode.name}</h3>
                <p className="text-[9px] font-mono text-sentinel-accent/50 mt-0.5 uppercase tracking-widest">
                  {hoveredNode.kind ?? "service"} · {hoveredNode.id.slice(0, 28)}
                </p>
              </div>
              <span className={`text-[9px] px-1.5 py-0.5 rounded font-mono uppercase tracking-widest ${
                hoveredNode.health === "critical" ? "badge-critical" :
                hoveredNode.health === "degraded" ? "badge-high" : "badge-low"
              }`}>
                {hoveredNode.health ?? "healthy"}
              </span>
            </div>

            {/* Metrics */}
            <div className="space-y-2">
              {[
                { label: "CPU", icon: <Cpu className="w-3 h-3" />, val: hoveredNode.cpu_percent ?? 0 },
                { label: "MEM", icon: <HardDrive className="w-3 h-3" />, val: hoveredNode.memory_percent ?? 0 },
              ].map(({ label, icon, val }) => (
                <div key={label} className="flex items-center gap-2 text-xs font-mono">
                  <span className="text-gray-500 w-4">{icon}</span>
                  <span className="text-gray-500 w-8">{label}</span>
                  <div className="flex-1 h-1.5 bg-sentinel-900 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${val}%` }}
                      transition={{ duration: 0.5, ease: "easeOut" }}
                      className="h-full rounded-full"
                      style={{ background: val > 80 ? "#ef4444" : val > 55 ? "#f59e0b" : "#22d3ee" }}
                    />
                  </div>
                  <span className="text-sentinel-accent text-[10px] w-9 text-right tabular-nums">{val.toFixed(1)}%</span>
                </div>
              ))}
            </div>

            {/* Uptime */}
            <div className="mt-3 pt-2.5 border-t border-sentinel-700/40 flex items-center justify-between">
              <span className="text-[9px] text-gray-500 font-mono uppercase tracking-widest">Uptime</span>
              <span className="text-xs text-sentinel-success font-mono font-bold">{(hoveredNode.uptime_percent ?? 99.5).toFixed(2)}%</span>
            </div>

            {/* Blast radius warning */}
            {hoveredNode.in_blast_radius && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mt-2 flex items-center gap-2 px-2 py-1.5 rounded-lg bg-red-500/15 border border-red-500/30"
              >
                <AlertTriangle className="w-3 h-3 text-red-400 shrink-0" />
                <span className="text-[9px] font-mono text-red-400 uppercase tracking-widest">In Blast Radius</span>
              </motion.div>
            )}
            {hoveredNode.is_root_cause && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mt-2 flex items-center gap-2 px-2 py-1.5 rounded-lg bg-red-500/20 border border-red-500/50 glow-border-danger"
              >
                <AlertTriangle className="w-3 h-3 text-red-400 shrink-0 animate-pulse" />
                <span className="text-[9px] font-mono text-red-300 uppercase tracking-widest font-bold">Root Cause Node</span>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AdvancedTopologyVisualization;
