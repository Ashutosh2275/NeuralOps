import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import type { TopologyGraph } from "../../lib/api";

interface AdvancedTopologyNode extends d3.SimulationNodeDatum {
  id: string;
  name?: string;
  kind?: string;
  health?: "healthy" | "degraded" | "critical";
  cpu_percent?: number;
  memory_percent?: number;
  in_blast_radius?: boolean;
  is_root_cause?: boolean;
  uptime_percent?: number;
  incident_count?: number;
}

interface AdvancedTopologyLink {
  source: string;
  target: string;
  weight?: number;
  traffic_rate?: number;
  latency_ms?: number;
  error_rate?: number;
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

export const AdvancedTopologyVisualization: React.FC<AdvancedTopologyProps> = ({
  graph,
  width = 1000,
  height = 600,
  blastRadiusNodes = [],
  rootCause,
  showPressure = true,
  showHealth = true,
  showEdgeWeights = true,
  animateUpdates = true,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  useEffect(() => {
    if (!svgRef.current || !graph.nodes || graph.nodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // Prepare enhanced nodes with pressure and health data
    const nodes: AdvancedTopologyNode[] = graph.nodes.map((n: any) => ({
      ...n,
      id: n.id,
      name: n.name || n.id.split("/").pop() || n.id,
      health: n.health || "healthy",
      cpu_percent: n.cpu_percent || Math.random() * 100,
      memory_percent: n.memory_percent || Math.random() * 100,
      in_blast_radius: blastRadiusNodes.includes(n.id),
      is_root_cause: n.id === rootCause,
      uptime_percent: n.uptime_percent || 99.5,
      incident_count: n.incident_count || 0,
    }));

    // Prepare enhanced links with weights
    const links: AdvancedTopologyLink[] = (graph.edges || []).map((e: any) => ({
      source: e.source,
      target: e.target,
      weight: e.weight || 1,
      traffic_rate: e.traffic_rate || Math.random() * 1000,
      latency_ms: e.latency_ms || Math.random() * 100,
      error_rate: e.error_rate || Math.random() * 5,
      in_blast_radius: blastRadiusNodes.includes(e.source) && blastRadiusNodes.includes(e.target),
    }));

    // Create simulation
    const simulation = d3
      .forceSimulation(nodes)
      .force(
        "link",
        d3
          .forceLink(links as d3.SimulationLinkDatum<AdvancedTopologyNode>[])
          .id((d: any) => d.id)
          .distance((d: any) => 80 + (d.weight || 1) * 20)
          .strength(0.7)
      )
      .force("charge", d3.forceManyBody().strength(-300).distanceMax(500))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(40));

    // Main group
    const g = svg.append("g");

    // Add defs for gradients and markers
    const defs = svg.append("defs");

    // Arrow marker for links
    defs
      .append("marker")
      .attr("id", "arrow")
      .attr("markerWidth", 10)
      .attr("markerHeight", 10)
      .attr("refX", 25)
      .attr("refY", 3)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,0 L0,6 L9,3 Z")
      .attr("fill", "#3b82f6");

    // Health gradient
    const healthGradient = defs.append("linearGradient").attr("id", "health-gradient");
    healthGradient.append("stop").attr("offset", "0%").attr("stop-color", "#22c55e");
    healthGradient.append("stop").attr("offset", "100%").attr("stop-color", "#dc2626");

    // Pressure gradient (CPU/Memory)
    const pressureGradient = defs.append("linearGradient").attr("id", "pressure-gradient");
    pressureGradient.append("stop").attr("offset", "0%").attr("stop-color", "#3b82f6");
    pressureGradient.append("stop").attr("offset", "50%").attr("stop-color", "#f59e0b");
    pressureGradient.append("stop").attr("offset", "100%").attr("stop-color", "#ef4444");

    // Links group
    const linkGroup = g.append("g").attr("class", "links");

    // Background links (for blast radius)
    const blastLinks = linkGroup
      .selectAll("line.blast-link")
      .data(links.filter((l) => l.in_blast_radius))
      .join("line")
      .attr("class", "blast-link")
      .attr("stroke", "#ef4444")
      .attr("stroke-opacity", 0.3)
      .attr("stroke-width", 3)
      .attr("stroke-dasharray", "5,5");

    // Regular links
    const regularLinks = linkGroup
      .selectAll("line.regular-link")
      .data(links.filter((l) => !l.in_blast_radius))
      .join("line")
      .attr("class", "regular-link")
      .attr("stroke", "#3b82f6")
      .attr("stroke-opacity", 0.4)
      .attr("stroke-width", (d: any) => Math.min(3, 1 + (d.weight || 1) * 0.5))
      .attr("marker-end", "url(#arrow)");

    // Link labels (edge weights/traffic)
    const linkLabels = linkGroup
      .selectAll("text.link-label")
      .data(showEdgeWeights ? links : [])
      .join("text")
      .attr("class", "link-label")
      .attr("font-size", 9)
      .attr("fill", "#cbd5e1")
      .attr("text-anchor", "middle")
      .attr("opacity", 0.6)
      .text((d: any) => `${d.traffic_rate?.toFixed(0) || 0} req/s`);

    // Nodes group
    const nodeGroup = g.append("g").attr("class", "nodes");

    // Blast radius circles
    const blastCircles = nodeGroup
      .selectAll("circle.blast-radius")
      .data(nodes.filter((n) => n.in_blast_radius))
      .join("circle")
      .attr("class", "blast-radius")
      .attr("r", 35)
      .attr("fill", "none")
      .attr("stroke", "#ef4444")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "5,5")
      .attr("opacity", 0.5);

    // Node circles (pressure visualization)
    const nodeCircles = nodeGroup
      .selectAll("circle.node-main")
      .data(nodes)
      .join("circle")
      .attr("class", "node-main")
      .attr("r", (d: any) => {
        if (d.is_root_cause) return 16;
        if (d.kind === "Pod") return 10;
        return 12;
      })
      .attr("fill", (d: any) => {
        if (d.is_root_cause) return "#ef4444";
        if (showPressure) {
          const avgPressure = ((d.cpu_percent || 0) + (d.memory_percent || 0)) / 2;
          if (avgPressure > 80) return "#ef4444";
          if (avgPressure > 60) return "#f59e0b";
          if (avgPressure > 40) return "#eab308";
          return "#22c55e";
        }
        if (showHealth) {
          if (d.health === "critical") return "#ef4444";
          if (d.health === "degraded") return "#f59e0b";
          return "#22c55e";
        }
        return d.kind === "Pod" ? "#06b6d4" : "#3b82f6";
      })
      .attr("opacity", (d: any) => (d.in_blast_radius ? 1 : 0.8))
      .attr("cursor", "pointer")
      .on("mouseenter", (e: any, d: any) => {
        setHoveredNode(d.id);
      })
      .on("mouseleave", () => {
        setHoveredNode(null);
      })
      .on("click", (e: any, d: any) => {
        e.stopPropagation();
        setSelectedNode(d.id === selectedNode ? null : d.id);
      });

    // Health indicator rings
    if (showHealth) {
      nodeGroup
        .selectAll("circle.health-ring")
        .data(nodes)
        .join("circle")
        .attr("class", "health-ring")
        .attr("r", (d: any) => {
          if (d.is_root_cause) return 20;
          if (d.kind === "Pod") return 13;
          return 15;
        })
        .attr("fill", "none")
        .attr("stroke", (d: any) => {
          if (d.health === "critical") return "#fca5a5";
          if (d.health === "degraded") return "#fcd34d";
          return "#86efac";
        })
        .attr("stroke-width", 1)
        .attr("opacity", 0.5);
    }

    // Node labels
    const labels = nodeGroup
      .selectAll("text.node-label")
      .data(nodes)
      .join("text")
      .attr("class", "node-label")
      .text((d: any) => d.name)
      .attr("font-size", 10)
      .attr("fill", "#cbd5e1")
      .attr("text-anchor", "middle")
      .attr("dy", (d: any) => (d.is_root_cause ? -22 : -18))
      .attr("pointer-events", "none");

    // Tooltip group
    const tooltip = d3
      .select("body")
      .append("div")
      .style("position", "absolute")
      .style("padding", "8px 12px")
      .style("background", "rgba(15, 23, 42, 0.95)")
      .style("color", "#cbd5e1")
      .style("border", "1px solid rgba(59, 130, 246, 0.5)")
      .style("border-radius", "4px")
      .style("font-size", "11px")
      .style("font-family", '"JetBrains Mono", monospace')
      .style("pointer-events", "none")
      .style("z-index", "1000")
      .style("display", "none")
      .style("max-width", "200px");

    nodeCircles.on("mousemove", (e: any, d: any) => {
      const tooltipContent = `
        <div style="font-weight: 600; color: #60a5fa;">${d.name}</div>
        <div style="margin-top: 4px; font-size: 10px;">
          <div>Kind: ${d.kind || "Unknown"}</div>
          <div>Health: <span style="color: ${d.health === "healthy" ? "#22c55e" : d.health === "degraded" ? "#f59e0b" : "#ef4444"}">${d.health?.toUpperCase()}</span></div>
          ${showPressure ? `
            <div>CPU: <span style="color: ${(d.cpu_percent || 0) > 80 ? "#ef4444" : "#22c55e"}">${d.cpu_percent?.toFixed(1) || 0}%</span></div>
            <div>Memory: <span style="color: ${(d.memory_percent || 0) > 80 ? "#ef4444" : "#22c55e"}">${d.memory_percent?.toFixed(1) || 0}%</span></div>
          ` : ""}
          <div>Uptime: ${d.uptime_percent?.toFixed(2) || 99.9}%</div>
          <div>Incidents: ${d.incident_count || 0}</div>
          ${d.is_root_cause ? '<div style="color: #ef4444; margin-top: 4px;">🔴 ROOT CAUSE</div>' : ""}
          ${d.in_blast_radius ? '<div style="color: #ef4444; margin-top: 4px;">💥 BLAST RADIUS</div>' : ""}
        </div>
      `;

      tooltip.html(tooltipContent).style("display", "block").style("left", e.pageX + 10 + "px").style("top", e.pageY + 10 + "px");
    });

    nodeCircles.on("mouseleave", () => {
      tooltip.style("display", "none");
    });

    // Simulation tick
    simulation.on("tick", () => {
      blastCircles.attr("cx", (d: any) => d.x ?? 0).attr("cy", (d: any) => d.y ?? 0);

      nodeCircles.attr("cx", (d: any) => d.x ?? 0).attr("cy", (d: any) => d.y ?? 0);

      nodeGroup
        .selectAll("circle.health-ring")
        .attr("cx", (d: any) => d.x ?? 0)
        .attr("cy", (d: any) => d.y ?? 0);

      labels.attr("x", (d: any) => d.x ?? 0).attr("y", (d: any) => d.y ?? 0);

      blastLinks
        .attr("x1", (d: any) => (d.source as AdvancedTopologyNode).x ?? 0)
        .attr("y1", (d: any) => (d.source as AdvancedTopologyNode).y ?? 0)
        .attr("x2", (d: any) => (d.target as AdvancedTopologyNode).x ?? 0)
        .attr("y2", (d: any) => (d.target as AdvancedTopologyNode).y ?? 0);

      regularLinks
        .attr("x1", (d: any) => (d.source as AdvancedTopologyNode).x ?? 0)
        .attr("y1", (d: any) => (d.source as AdvancedTopologyNode).y ?? 0)
        .attr("x2", (d: any) => (d.target as AdvancedTopologyNode).x ?? 0)
        .attr("y2", (d: any) => (d.target as AdvancedTopologyNode).y ?? 0);

      linkLabels
        .attr("x", (d: any) => {
          const sx = (d.source as AdvancedTopologyNode).x ?? 0;
          const tx = (d.target as AdvancedTopologyNode).x ?? 0;
          return (sx + tx) / 2;
        })
        .attr("y", (d: any) => {
          const sy = (d.source as AdvancedTopologyNode).y ?? 0;
          const ty = (d.target as AdvancedTopologyNode).y ?? 0;
          return (sy + ty) / 2;
        });
    });

    return () => {
      simulation.stop();
      tooltip.remove();
    };
  }, [graph, width, height, blastRadiusNodes, rootCause, showPressure, showHealth, showEdgeWeights]);

  return (
    <div style={{ position: "relative" }}>
      <svg
        ref={svgRef}
        width={width}
        height={height}
        style={{
          background: "rgba(15, 23, 42, 0.8)",
          border: "1px solid rgba(148, 163, 184, 0.1)",
          borderRadius: "8px",
        }}
      />

      {/* Legend */}
      <div
        style={{
          position: "absolute",
          bottom: "16px",
          left: "16px",
          background: "rgba(15, 23, 42, 0.9)",
          border: "1px solid rgba(148, 163, 184, 0.1)",
          borderRadius: "6px",
          padding: "12px",
          fontSize: "11px",
          color: "#cbd5e1",
        }}
      >
        <div style={{ marginBottom: "8px", fontWeight: 600, color: "#60a5fa" }}>Legend</div>
        <div style={{ marginBottom: "4px" }}>🔴 Red: Critical | 🟠 Orange: Degraded | 🟢 Green: Healthy</div>
        <div style={{ marginBottom: "4px" }}>📦 Pod | ☁️ Service</div>
        <div>💥 Dashed circle = Blast radius</div>
      </div>

      {/* Info Panel */}
      {selectedNode && (
        <div
          style={{
            position: "absolute",
            top: "16px",
            right: "16px",
            background: "rgba(15, 23, 42, 0.9)",
            border: "1px solid rgba(59, 130, 246, 0.3)",
            borderRadius: "6px",
            padding: "12px",
            fontSize: "11px",
            color: "#cbd5e1",
            maxWidth: "250px",
          }}
        >
          <div style={{ fontWeight: 600, color: "#60a5fa", marginBottom: "8px" }}>Selected Node</div>
          <div>ID: {selectedNode}</div>
          <button
            onClick={() => setSelectedNode(null)}
            style={{
              marginTop: "8px",
              padding: "6px 12px",
              background: "rgba(59, 130, 246, 0.2)",
              border: "1px solid rgba(59, 130, 246, 0.5)",
              color: "#60a5fa",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "10px",
            }}
          >
            Close
          </button>
        </div>
      )}
    </div>
  );
};

export default AdvancedTopologyVisualization;
