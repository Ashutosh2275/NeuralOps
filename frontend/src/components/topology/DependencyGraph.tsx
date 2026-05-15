import { useEffect, useRef } from "react";
import * as d3 from "d3";
import type { TopologyGraph } from "../../lib/api";

interface Props {
  graph: TopologyGraph;
  width?: number;
  height?: number;
}

export default function DependencyGraph({ graph, width = 800, height = 500 }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || graph.nodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const nodes = graph.nodes.map((n) => ({ ...n, id: n.id }));
    const links = graph.edges.map((e) => ({ source: e.source, target: e.target }));

    const simulation = d3
      .forceSimulation(nodes as d3.SimulationNodeDatum[])
      .force("link", d3.forceLink(links).id((d) => (d as { id: string }).id).distance(80))
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(width / 2, height / 2));

    const g = svg.append("g");

    const link = g
      .append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", "#3b82f6")
      .attr("stroke-opacity", 0.6);

    const node = g
      .append("g")
      .selectAll("circle")
      .data(nodes)
      .join("circle")
      .attr("r", 8)
      .attr("fill", (d) => (d.kind === "Pod" ? "#22d3ee" : "#3b82f6"));

    const label = g
      .append("g")
      .selectAll("text")
      .data(nodes)
      .join("text")
      .text((d) => d.name ?? d.id.split("/").pop() ?? d.id)
      .attr("font-size", 10)
      .attr("fill", "#94a3b8")
      .attr("dx", 12)
      .attr("dy", 4);

    simulation.on("tick", () => {
      link
        .attr("x1", (d) => (d.source as d3.SimulationNodeDatum).x ?? 0)
        .attr("y1", (d) => (d.source as d3.SimulationNodeDatum).y ?? 0)
        .attr("x2", (d) => (d.target as d3.SimulationNodeDatum).x ?? 0)
        .attr("y2", (d) => (d.target as d3.SimulationNodeDatum).y ?? 0);
      node.attr("cx", (d) => d.x ?? 0).attr("cy", (d) => d.y ?? 0);
      label.attr("x", (d) => d.x ?? 0).attr("y", (d) => d.y ?? 0);
    });

    return () => {
      simulation.stop();
    };
  }, [graph, width, height]);

  return (
    <svg ref={svgRef} width={width} height={height} className="bg-sentinel-900 rounded-lg border border-sentinel-700" />
  );
}
