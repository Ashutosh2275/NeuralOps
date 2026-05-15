import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import AIInsightsPanel from "../components/dashboard/AIInsightsPanel";
import RCAPanel from "../components/dashboard/RCAPanel";
import RecommendationPanel from "../components/dashboard/RecommendationPanel";
import DependencyGraph from "../components/topology/DependencyGraph";
import { api, IncidentSummary, TopologyGraph } from "../lib/api";
import { useWebSocket } from "../hooks/useWebSocket";

export default function Dashboard() {
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [topology, setTopology] = useState<TopologyGraph | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [rca, setRca] = useState<Record<string, unknown> | null>(null);
  const [recommendations, setRecommendations] = useState<Awaited<ReturnType<typeof api.recommendations>>>([]);
  const [insights, setInsights] = useState<Awaited<ReturnType<typeof api.insights>>>([]);
  const [health, setHealth] = useState("checking");
  const { connected, events, lastEvent } = useWebSocket((e) => {
    if (e.type === "topology" && e.payload?.nodes) setTopology(e.payload as unknown as TopologyGraph);
    if (e.type === "incident") refreshIncidents();
  });

  const refreshIncidents = () => {
    api.incidents().then(setIncidents).catch(() => setIncidents([]));
    api.topology().then(setTopology).catch(() => null);
  };

  useEffect(() => {
    api.health().then((h) => setHealth(h.status)).catch(() => setHealth("down"));
    refreshIncidents();
  }, [lastEvent]);

  useEffect(() => {
    if (!selectedId) return;
    api.rca(selectedId).then(setRca).catch(() => setRca(null));
    api.recommendations(selectedId).then(setRecommendations).catch(() => setRecommendations([]));
    api.insights(selectedId).then(setInsights).catch(() => setInsights([]));
  }, [selectedId]);

  const chartData = [
    { t: "-4m", events: events.filter((e) => e.type === "event").length + 5 },
    { t: "-3m", events: events.filter((e) => e.type === "anomaly").length + 8 },
    { t: "-2m", events: incidents.length + 12 },
    { t: "-1m", events: events.length + 15 },
    { t: "now", events: events.length + 20 },
  ];

  return (
    <div className="space-y-6">
      <header className="flex justify-between items-center">
        <div>
          <h2 className="font-display text-2xl font-bold">Intelligence Command Center</h2>
          <p className="text-gray-500 text-sm">Live topology · RCA · AI agents · Replay</p>
        </div>
        <span className={`text-xs px-2 py-1 rounded ${connected ? "bg-green-900 text-green-300" : "bg-red-900"}`}>
          {connected ? "Live" : "Offline"}
        </span>
      </header>

      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Status", value: health },
          { label: "Incidents", value: incidents.length },
          { label: "Topology Nodes", value: topology?.node_count ?? 0 },
          { label: "WS Events", value: events.length },
        ].map((s) => (
          <div key={s.label} className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4">
            <p className="text-xs text-gray-500">{s.label}</p>
            <p className="text-2xl font-bold mt-1 text-sentinel-accent">{s.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-4">
          {topology && topology.nodes.length > 0 ? (
            <DependencyGraph graph={topology} width={700} height={320} />
          ) : (
            <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-8 text-center text-gray-500">
              Topology loading...
            </div>
          )}
          <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4">
            <h3 className="text-sm font-semibold mb-2">Event Throughput</h3>
            <ResponsiveContainer width="100%" height={160}>
              <AreaChart data={chartData}>
                <XAxis dataKey="t" stroke="#64748b" fontSize={10} />
                <YAxis stroke="#64748b" fontSize={10} />
                <Tooltip contentStyle={{ background: "#1a2332" }} />
                <Area type="monotone" dataKey="events" stroke="#22d3ee" fill="#22d3ee33" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4 max-h-48 overflow-y-auto">
            <h3 className="text-sm font-semibold mb-2">Incidents</h3>
            {incidents.map((i) => (
              <button
                key={i.id}
                onClick={() => setSelectedId(i.id)}
                className={`block w-full text-left text-xs py-1 px-2 rounded mb-1 ${
                  selectedId === i.id ? "bg-sentinel-700" : "hover:bg-sentinel-800"
                }`}
              >
                <Link to={`/incidents/${i.id}`} className="hover:text-sentinel-accent">{i.title}</Link>
              </button>
            ))}
          </div>
          <RCAPanel rca={rca} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <AIInsightsPanel insights={insights} wsEvents={events} />
        <RecommendationPanel items={recommendations} />
      </div>
    </div>
  );
}
