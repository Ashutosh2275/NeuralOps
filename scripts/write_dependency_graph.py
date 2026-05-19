import os

file_path = "frontend/src/components/topology/DependencyGraph.tsx"

content = """import React, { useEffect, useRef, memo } from "react";
import * as d3 from "d3";
import type { TopologyGraph } from "../../lib/api";

interface Props {
  graph: TopologyGraph;
  width?: number;
  height?: number;
}

interface TopoNode extends d3.SimulationNodeDatum {
  id: string;
  name?: string;
  kind?: string;
  health?: "healthy" | "warning" | "critical" | string;
}

interface TopoLink extends d3.SimulationLinkDatum<TopoNode> {
  source: string | TopoNode;
  target: string | TopoNode;
}

function DependencyGraph({ graph, width = 800, height = 500 }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  
  const simRef = useRef<d3.Simulation<TopoNode, TopoLink> | null>(null);
  const linkGRef = useRef<d3.Selection<SVGGElement, unknown, null, undefined> | null>(null);
  const nodeGRef = useRef<d3.Selection<SVGGElement, unknown, null, undefined> | null>(null);
  const labelGRef = useRef<d3.Selection<SVGGElement, unknown, null, undefined> | null>(null);

  useEffect(() => {
    if (!svgRef.current) return;
    if (simRef.current) return;
    
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const g = svg.append("g");
    const zoom = d3.zoom<SVGSVGElement, unknown>().scaleExtent([0.1, 4])
      .on("zoom", (e) => g.attr("transform", e.transform));
    svg.call(zoom);

    linkGRef.current = g.append("g").attr("class", "links");
    nodeGRef.current = g.append("g").attr("class", "nodes");
    labelGRef.current = g.append("g").attr("class", "labels");

    simRef.current = d3.forceSimulation<TopoNode>()
      .force("link", d3.forceLink<TopoNode, TopoLink>().id(d => d.id).distance(80))
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(width / 2, height / 2).strength(0.05))
      .force("collision", d3.forceCollide().radius(30));

    return () => {
      if (simRef.current) simRef.current.stop();
      simRef.current = null;
    };
  }, [width, height]);


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
      .attr("stroke", "#475569").attr("stroke-width", 1.5).attr("opacity", 0);
      
    linkEnter.merge(linkSel).transition().duration(300).attr("opacity", 0.8);
    linkSel.exit().remove();

    // ── Nodes ──
    const nodeSel = nodeGRef.current.selectAll<SVGCircleElement, TopoNode>("circle").data(nodes, d => d.id);
    const nodeEnter = nodeSel.enter().append("circle")
      .attr("r", 20)
      .attr("cursor", "pointer")
      .call(d3.drag<SVGCircleElement, TopoNode>()
        .on("start", (e, d) => { if (!e.active) simRef.current!.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on("drag",  (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on("end",   (e, d) => { if (!e.active) simRef.current!.alphaTarget(0); d.fx = null; d.fy = null; })
      );

    nodeEnter.merge(nodeSel).transition().duration(300)
      .attr("fill", d => {
        if (d.kind === "Pod") return "#3b82f6";
        if (d.kind === "Service") return "#8b5cf6";
        return "#64748b";
      })
      .attr("stroke", "#0f172a")
      .attr("stroke-width", 2);
      
    nodeSel.exit().remove();

    // ── Labels ──
    const labelSel = labelGRef.current.selectAll<SVGTextElement, TopoNode>("text").data(nodes, d => d.id);
    labelSel.enter().append("text")
      .attr("text-anchor", "middle").attr("dy", "0.3em").attr("font-size", "10px").attr("fill", "#f8fafc")
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

  }, [graph]);

  return (
    <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg overflow-hidden w-full h-full min-h-[400px]">
      <svg ref={svgRef} className="w-full h-full" />
    </div>
  );
}
export default memo(DependencyGraph);
"""

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("DependencyGraph written successfully!")