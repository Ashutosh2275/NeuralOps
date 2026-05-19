import os

file_path = "frontend/src/components/topology/LiveTopology.tsx"

content = """import React, { useEffect, useRef, useState, memo } from "react";
import * as d3 from "d3";
import { TopologyGraph, TopologyNode, TopologyEdge } from "../../lib/api";

interface TopoNode extends d3.SimulationNodeDatum {
  id: string;
  name?: string;
  health?: "healthy" | "warning" | "critical" | string;
}

interface TopoLink extends d3.SimulationLinkDatum<TopoNode> {
  source: string | TopoNode;
  target: string | TopoNode;
  health?: "healthy" | "warning" | "critical" | string;
}

interface LiveTopologyProps {
  graph: TopologyGraph | null;
  cascadingFailures?: Set<string>;
  selectedNode?: string;
  onNodeSelect?: (nodeId: string) => void;
}

function LiveTopology({
  graph,
  cascadingFailures = new Set(),
  selectedNode,
  onNodeSelect,
}: LiveTopologyProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  const simRef = useRef<d3.Simulation<TopoNode, TopoLink> | null>(null);
  const nodeGRef = useRef<d3.Selection<SVGGElement, unknown, null, undefined> | null>(null);
  const linkGRef = useRef<d3.Selection<SVGGElement, unknown, null, undefined> | null>(null);
  const labelGRef = useRef<d3.Selection<SVGGElement, unknown, null, undefined> | null>(null);

  const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());

  // Init
  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;
    if (simRef.current) return; // already initialized

    const width = containerRef.current.clientWidth || 800;
    const height = containerRef.current.clientHeight || 500;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
    svg.attr("viewBox", `0 0 ${width} ${height}`);

    svg.append("defs").selectAll("marker")
      .data(["healthy", "warning", "critical", "danger"])
      .enter().append("marker")
      .attr("id", d => `arrow-${d}`)
      .attr("markerWidth", 10).attr("markerHeight", 10)
      .attr("refX", 28).attr("refY", 5).attr("orient", "auto")
      .append("path").attr("d", "M0,0 L10,5 L0,10")
      .attr("fill", d => {
        if (d === "critical" || d === "danger") return "#ef4444";
        if (d === "warning") return "#eab308";
        return "#10b981";
      });

    const g = svg.append("g");
    
    // Zoom
    const zoom = d3.zoom<SVGSVGElement, unknown>().scaleExtent([0.1, 4])
      .on("zoom", (e) => g.attr("transform", e.transform));
    svg.call(zoom);

    linkGRef.current = g.append("g").attr("class", "links");
    nodeGRef.current = g.append("g").attr("class", "nodes");
    labelGRef.current = g.append("g").attr("class", "labels");

    simRef.current = d3.forceSimulation<TopoNode>()
      .force("link", d3.forceLink<TopoNode, TopoLink>().id(d => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2).strength(0.05))
      .force("collision", d3.forceCollide().radius(40));

    return () => {
      if (simRef.current) simRef.current.stop();
      simRef.current = null;
    };
  }, []);

  // Update
  useEffect(() => {
    if (!graph || !graph.nodes || !simRef.current || !nodeGRef.current || !linkGRef.current || !labelGRef.current) return;

    const nodes: TopoNode[] = (graph.nodes as any[]).map(n => ({
      ...n,
      id: String(n.id)
    }));
    
    const links: TopoLink[] = (graph.edges as any[]).map(e => ({
      ...e,
      source: String(e.source),
      target: String(e.target)
    }));

    // Preserve positions
    const oldNodes = simRef.current.nodes();
    const nodeMap = new Map(oldNodes.map(n => [n.id, n]));
    nodes.forEach(n => {
      const old = nodeMap.get(n.id);
      if (old) { n.x = old.x; n.y = old.y; n.vx = old.vx; n.vy = old.vy; }
    });

    simRef.current.nodes(nodes);
    (simRef.current.force("link") as d3.ForceLink<TopoNode, TopoLink>).links(links);
    simRef.current.alpha(0.05).restart();

    // ── Links ──
    const linkSel = linkGRef.current.selectAll<SVGLineElement, TopoLink>("line")
      .data(links, d => `${(d.source as any).id || d.source}-${(d.target as any).id || d.target}`);
      
    const linkEnter = linkSel.enter().append("line")
      .attr("stroke-width", 2).attr("opacity", 0);
      
    linkEnter.merge(linkSel).transition().duration(300)
      .attr("opacity", 0.6)
      .attr("stroke", d => {
        if (d.health === "critical") return "#ef4444";
        if (d.health === "warning") return "#eab308";
        return "#64748b";
      })
      .attr("marker-end", d => `url(#arrow-${d.health || "healthy"})`);
      
    linkSel.exit().remove();

    // ── Nodes ──
    const nodeSel = nodeGRef.current.selectAll<SVGCircleElement, TopoNode>("circle").data(nodes, d => d.id);
    
    const nodeEnter = nodeSel.enter().append("circle")
      .attr("r", 25)
      .attr("cursor", "pointer")
      .call(d3.drag<SVGCircleElement, TopoNode>()
        .on("start", (e, d) => { if (!e.active) simRef.current!.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on("drag",  (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on("end",   (e, d) => { if (!e.active) simRef.current!.alphaTarget(0); d.fx = null; d.fy = null; })
      )
      .on("click", (_, d) => {
        if (onNodeSelect) onNodeSelect(d.id);
      });

    nodeEnter.merge(nodeSel).transition().duration(300)
      .attr("fill", d => {
        if (cascadingFailures.has(d.id)) return "#dc2626";
        if (d.health === "critical") return "#ef4444";
        if (d.health === "warning") return "#eab308";
        return "#10b981";
      })
      .attr("stroke", d => selectedNode === d.id ? "#ffffff" : "none")
      .attr("stroke-width", 2);
      
    nodeSel.exit().remove();

    // ── Labels ──
    const labelSel = labelGRef.current.selectAll<SVGTextElement, TopoNode>("text").data(nodes, d => d.id);
    
    labelSel.enter().append("text")
      .attr("text-anchor", "middle").attr("dy", "0.3em").attr("font-size", "12px").attr("fill", "#ffffff").attr("font-weight", "bold")
      .style("pointer-events", "none")
      .merge(labelSel)
      .text(d => d.name || d.id.split("/").pop() || "?");
      
    labelSel.exit().remove();

    // Tick
    simRef.current.on("tick", () => {
      if (linkGRef.current) {
        linkGRef.current.selectAll<SVGLineElement, TopoLink>("line")
          .attr("x1", d => (d.source as TopoNode).x ?? 0).attr("y1", d => (d.source as TopoNode).y ?? 0)
          .attr("x2", d => (d.target as TopoNode).x ?? 0).attr("y2", d => (d.target as TopoNode).y ?? 0);
      }
      if (nodeGRef.current) {
        nodeGRef.current.selectAll<SVGCircleElement, TopoNode>("circle")
          .attr("cx", d => d.x ?? 0).attr("cy", d => d.y ?? 0);
      }
      if (labelGRef.current) {
        labelGRef.current.selectAll<SVGTextElement, TopoNode>("text")
          .attr("x", d => d.x ?? 0).attr("y", d => d.y ?? 0);
      }
    });

  }, [graph, cascadingFailures, selectedNode, onNodeSelect]);

  return (
    <div ref={containerRef} className="bg-sentinel-900 border border-sentinel-700 rounded-lg overflow-hidden w-full h-[500px]">
      <svg ref={svgRef} className="w-full h-full" />
    </div>
  );
}

export default memo(LiveTopology);
"""

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("LiveTopology File written successfully!")