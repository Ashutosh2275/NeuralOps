import os

file_path = "frontend/src/components/topology/CascadingFailureVisualizer.tsx"

content = """import React, { useEffect, useRef, memo } from "react";
import * as d3 from "d3";
import type { BlastRadiusEvent, ReplayFrame } from "../../lib/api";

interface Props {
  cascadeEvents: BlastRadiusEvent[];
  frame?: ReplayFrame;
}

interface TopoNode extends d3.SimulationNodeDatum {
  id: string;
  depth: number;
}
interface TopoLink extends d3.SimulationLinkDatum<TopoNode> {
  source: string | TopoNode;
  target: string | TopoNode;
}

function CascadingFailureVisualizer({ cascadeEvents, frame }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const simRef = useRef<d3.Simulation<TopoNode, TopoLink> | null>(null);
  const linkGRef = useRef<d3.Selection<SVGGElement, unknown, null, undefined> | null>(null);
  const nodeGRef = useRef<d3.Selection<SVGGElement, unknown, null, undefined> | null>(null);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;
    if (simRef.current) return;

    const width = containerRef.current.clientWidth || 800;
    const height = containerRef.current.clientHeight || 400;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const g = svg.append("g");
    const zoom = d3.zoom<SVGSVGElement, unknown>().scaleExtent([0.1, 4])
      .on("zoom", (e) => g.attr("transform", e.transform));
    svg.call(zoom);

    linkGRef.current = g.append("g").attr("class", "links");
    nodeGRef.current = g.append("g").attr("class", "nodes");

    simRef.current = d3.forceSimulation<TopoNode>()
      .force("link", d3.forceLink<TopoNode, TopoLink>().id(d => d.id).distance(150))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2).strength(0.05))
      .force("collision", d3.forceCollide().radius(40));

    return () => {
      if (simRef.current) simRef.current.stop();
      simRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!cascadeEvents?.length || !simRef.current || !nodeGRef.current || !linkGRef.current) return;

    const nodesMap = new Map<string, TopoNode>();
    const links: TopoLink[] = [];

    cascadeEvents.forEach(evt => {
      if (!nodesMap.has(evt.source_node)) nodesMap.set(evt.source_node, { id: evt.source_node, depth: evt.cascade_depth });
      if (!nodesMap.has(evt.affected_node)) nodesMap.set(evt.affected_node, { id: evt.affected_node, depth: evt.cascade_depth });
      links.push({
        source: evt.source_node,
        target: evt.affected_node
      });
    });

    const nodes = Array.from(nodesMap.values());

    const oldNodes = simRef.current.nodes();
    const mapMatch = new Map(oldNodes.map(n => [n.id, n]));
    nodes.forEach(n => {
      const old = mapMatch.get(n.id);
      if (old) { n.x = old.x; n.y = old.y; n.vx = old.vx; n.vy = old.vy; }
    });

    simRef.current.nodes(nodes);
    (simRef.current.force("link") as d3.ForceLink<TopoNode, TopoLink>).links(links);
    simRef.current.alpha(0.05).restart();

    // ── Links ──
    const linkSel = linkGRef.current.selectAll<SVGLineElement, TopoLink>("line")
      .data(links, d => `${(d.source as any).id || d.source}-${(d.target as any).id || d.target}`);
      
    const linkEnter = linkSel.enter().append("line")
      .attr("stroke", "#ef4444").attr("stroke-width", 2).attr("opacity", 0)
      .attr("stroke-dasharray", "5 5");
      
    linkEnter.merge(linkSel).transition().duration(300).attr("opacity", 0.6);
    linkSel.exit().remove();

    // ── Nodes ──
    const nodeSel = nodeGRef.current.selectAll<SVGGElement, TopoNode>("g").data(nodes, d => d.id);
    const nodeEnter = nodeSel.enter().append("g")
      .attr("cursor", "pointer")
      .call(d3.drag<SVGGElement, TopoNode>()
        .on("start", (e, d) => { if (!e.active) simRef.current!.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on("drag",  (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on("end",   (e, d) => { if (!e.active) simRef.current!.alphaTarget(0); d.fx = null; d.fy = null; })
      );

    nodeEnter.append("circle").attr("class", "main").attr("r", 25);
    nodeEnter.append("circle").attr("class", "pulse")
      .attr("r", 25).attr("fill", "none")
      .attr("stroke", "#ef4444").attr("stroke-width", 2)
      .append("animate").attr("attributeName", "r").attr("values", "25;40;25")
      .attr("dur", "2s").attr("repeatCount", "indefinite");

    nodeEnter.append("text").attr("text-anchor", "middle").attr("dy", "0.3em")
      .attr("font-size", "12px").attr("fill", "#ffffff").attr("font-weight", "bold")
      .style("pointer-events", "none");

    const nodeUpdate = nodeEnter.merge(nodeSel);
    
    nodeUpdate.select(".main").transition().duration(300)
      .attr("fill", d => d.depth === 0 ? "#7f1d1d" : "#dc2626")
      .attr("stroke", d => d.depth === 0 ? "#fca5a5" : "#f87171")
      .attr("stroke-width", 2);

    nodeUpdate.select("text").text(d => d.id.split("/").pop() || "?");

    nodeSel.exit().remove();

    simRef.current.on("tick", () => {
      if (linkGRef.current) {
        linkGRef.current.selectAll<SVGLineElement, TopoLink>("line")
          .attr("x1", d => (d.source as TopoNode).x ?? 0).attr("y1", d => (d.source as TopoNode).y ?? 0)
          .attr("x2", d => (d.target as TopoNode).x ?? 0).attr("y2", d => (d.target as TopoNode).y ?? 0);
      }
      if (nodeGRef.current) {
        nodeGRef.current.selectAll<SVGGElement, TopoNode>("g")
          .attr("transform", d => `translate(${d.x ?? 0},${d.y ?? 0})`);
      }
    });

  }, [cascadeEvents]);

  return (
    <div ref={containerRef} className="bg-sentinel-900 border border-sentinel-700 rounded-lg overflow-hidden w-full h-[400px]">
      <svg ref={svgRef} className="w-full h-full" />
    </div>
  );
}
export default memo(CascadingFailureVisualizer);
"""

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("CascadingFailureVisualizer written successfully!")