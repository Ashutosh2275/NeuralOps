import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api";
import { useWebSocket } from "../hooks/useWebSocket";
import AIInsightsPanel from "../components/dashboard/AIInsightsPanel";
import RCAPanel from "../components/dashboard/RCAPanel";
import RecommendationPanel from "../components/dashboard/RecommendationPanel";
import ConfidenceVisualization from "../components/dashboard/ConfidenceVisualization";
import AIAssistantPanel from "../components/dashboard/AIAssistantPanel";

export default function IncidentDetail() {
  const { id } = useParams<{ id: string }>();
  const [incident, setIncident] = useState<Record<string, unknown> | null>(null);
  const { events } = useWebSocket();
  const [insights, setInsights] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [confidences, setConfidences] = useState<any[]>([]);

  useEffect(() => {
    if (id) api.incident(id).then(setIncident).catch(() => setIncident(null));
  }, [id]);

  useEffect(() => {
    const aiInsights = events
      .filter((e) => e.type === "ai_insight")
      .map((e) => ({
        agent: e.payload?.agent || "unknown",
        findings: e.payload?.findings || [],
        confidence: e.payload?.confidence || 0,
        reasoning: e.payload?.reasoning || "",
      }));
    setInsights(aiInsights);

    const recs = events
      .filter((e) => e.type === "recommendations")
      .flatMap((e) => e.payload || []);
    setRecommendations(recs);

    const confs = aiInsights.map((i) => ({
      agent: i.agent,
      confidence: i.confidence,
      success: true,
    }));
    setConfidences(confs);
  }, [events]);

  if (!incident) return <p className="text-gray-500">Loading...</p>;

  const timeline = (incident.timeline as { timestamp: string; title: string; type: string }[]) ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/incidents" className="text-gray-500 hover:text-sentinel-accent text-sm">
          Back
        </Link>
        <Link
          to={`/replay/${id}`}
          className="text-sm bg-sentinel-700 px-3 py-1 rounded hover:bg-sentinel-500"
        >
          Replay Incident
        </Link>
      </div>
      <h2 className="font-display text-2xl font-bold">{String(incident.title)}</h2>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">
          <RCAPanel rca={incident as any} />
          <RecommendationPanel items={recommendations} />
        </div>
        <div className="space-y-6">
          <AIInsightsPanel insights={insights} wsEvents={events} />
          <ConfidenceVisualization confidences={confidences} title="Analysis Confidence" />
        </div>
      </div>

      <AIAssistantPanel wsEvents={events} />

      <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold mb-4">Incident Timeline</h3>
        <ul className="space-y-2 border-l-2 border-sentinel-700 pl-4">
          {timeline.map((t, i) => (
            <li key={i} className="text-sm">
              <span className="text-gray-500 text-xs">{t.timestamp}</span>
              <p>{t.title}</p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
