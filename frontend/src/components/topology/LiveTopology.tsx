import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import { TopologyGraph, TopologyNode, TopologyEdge } from "../../lib/api";

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
  const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!graph || !svgRef.current) return;

    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    // Create simulation
    const simulation = d3
      .forceSimulation(graph.nodes as any)
      .force("link", d3.forceLink(graph.edges as any).id((d: any) => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(40));

    // Clear previous content
    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3.select(svgRef.current).attr("width", width).attr("height", height);

    // Create arrow markers for edges
    svg
      .append("defs")
      .selectAll("marker")
      .data(["healthy", "warning", "critical"])
      .enter()
      .append("marker")
      .attr("id", (d: any) => `arrow-${d}`)
      .attr("markerWidth", 10)
      .attr("markerHeight", 10)
      .attr("refX", 25)
      .attr("refY", 5)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,0 L10,5 L0,10")
      .attr("fill", (d: any) => {
        if (d === "critical") return "#ef4444";
        if (d === "warning") return "#eab308";
        return "#10b981";
      });

    // Links
    const links = svg
      .selectAll("line")
      .data(graph.edges)
      .enter()
      .append("line")
      .attr("stroke", (d: any) => {
        if (d.health === "critical") return "#ef4444";
        if (d.health === "warning") return "#eab308";
        return "#64748b";
      })
      .attr("stroke-width", 2)
      .attr("marker-end", (d: any) => `url(#arrow-${d.health || "healthy"})`)
      .attr("opacity", 0.6);

    // Nodes
    const nodes = svg
      .selectAll("circle")
      .data(graph.nodes)
      .enter()
      .append("circle")
      .attr("r", 25)
      .attr("fill", (d: any) => {
        if (cascadingFailures.has(d.id)) return "#dc2626";
        if (d.health === "critical") return "#ef4444";
        if (d.health === "warning") return "#eab308";
        return "#10b981";
      })
      .attr("stroke", (d: any) => (selectedNode === d.id ? "#ffffff" : "none"))
      .attr("stroke-width", 2)
      .attr("cursor", "pointer")
      .on("click", (_, d: any) => {
        onNodeSelect?.(d.id);
        setHighlightedNodes(new Set([d.id]));
      })
      .on("mouseover", (_, d: any) => {
        // Highlight connected nodes
        const connected = new Set<string>();
        connected.add(d.id);
        graph.edges.forEach((e) => {
          if (e.source === d.id) connected.add((e.target as unknown as TopologyNode).id);
          if (e.target === d.id) connected.add((e.source as unknown as TopologyNode).id);
        });
        setHighlightedNodes(connected);
      })
      .on("mouseout", () => {
        setHighlightedNodes(new Set([selectedNode || ""]));
      })
      .call(
        d3
          .drag<SVGCircleElement, any>()
          .on("start", (event: any, d: any) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event: any, d: any) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event: any, d: any) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    // Labels
    const labels = svg
      .selectAll("text")
      .data(graph.nodes)
      .enter()
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "0.3em")
      .attr("font-size", "12px")
      .attr("fill", "#ffffff")
      .attr("font-weight", "bold")
      .text((d: any) => d.name || d.id.split("/").pop() || "?");

    // Update positions on tick
    simulation.on("tick", () => {
      links
        .attr("x1", (d: any) => (d.source as any).x || 0)
        .attr("y1", (d: any) => (d.source as any).y || 0)
        .attr("x2", (d: any) => (d.target as any).x || 0)
        .attr("y2", (d: any) => (d.target as any).y || 0);

      nodes.attr("cx", (d: any) => d.x || 0).attr("cy", (d: any) => d.y || 0);

      labels.attr("x", (d: any) => d.x || 0).attr("y", (d: any) => d.y || 0);
    });
  }, [graph, cascadingFailures, selectedNode, onNodeSelect]);

  return (
    <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg overflow-hidden">
      <svg ref={svgRef} style={{ width: "100%", height: "500px" }} />
    </div>
  );
}
export default React.memo(LiveTopology);
