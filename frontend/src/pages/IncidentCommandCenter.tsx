import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { useWebSocket } from "../hooks/useWebSocket";
import IncidentFeed from "../components/dashboard/IncidentFeed";
import ActiveIncidentsPanel from "../components/dashboard/ActiveIncidentsPanel";
import HealthScoreCard from "../components/dashboard/HealthScoreCard";
import RCATimelinePanel from "../components/dashboard/RCATimelinePanel";
import CascadingFailureMap from "../components/dashboard/CascadingFailureMap";
import AIReasoningStream from "../components/dashboard/AIReasoningStream";
import RemediationActionsPanel from "../components/dashboard/RemediationActionsPanel";

export default function IncidentCommandCenter() {
  const { events } = useWebSocket();
  const [healthScore, setHealthScore] = useState<number>(100);
  const [incidents, setIncidents] = useState<any[]>([]);
  const [aiInsights, setAiInsights] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [remediationActions, setRemediationActions] = useState<any[]>([]);
  const [cascadingFailures, setCascadingFailures] = useState<any[]>([]);

  useEffect(() => {
    // Calculate health score based on active incidents
    const criticalCount = events.filter((e) => e.type === "incident" && e.payload?.severity === "critical").length;
    const errorCount = events.filter((e) => e.type === "incident" && e.payload?.severity === "error").length;
    const score = Math.max(0, 100 - criticalCount * 20 - errorCount * 5);
    setHealthScore(score);

    // Aggregate incidents
    const incidentsMap = new Map();
    events
      .filter((e) => e.type === "incident")
      .forEach((e) => {
        const id = e.payload?.incident_id;
        if (id && !incidentsMap.has(id)) {
          incidentsMap.set(id, e.payload);
        }
      });
    setIncidents(Array.from(incidentsMap.values()).slice(0, 20));

    // Aggregate AI insights
    const insightsMap = new Map();
    events
      .filter((e) => e.type === "ai_insight")
      .forEach((e, idx) => {
        insightsMap.set(idx, e.payload);
      });
    setAiInsights(Array.from(insightsMap.values()).slice(0, 15));

    // Aggregate recommendations
    const recsMap = new Map();
    events
      .filter((e) => e.type === "recommendations")
      .forEach((e, idx) => {
        if (Array.isArray(e.payload)) {
          e.payload.forEach((r, pidx) => {
            recsMap.set(`${idx}-${pidx}`, r);
          });
        }
      });
    setRecommendations(Array.from(recsMap.values()).slice(0, 10));

    // Aggregate cascading failures
    const cascadesMap = new Map();
    events
      .filter((e) => e.type === "cascading_failure")
      .forEach((e) => {
        const id = `${e.payload?.origin}-${Date.now()}`;
        if (!cascadesMap.has(id)) {
          cascadesMap.set(id, e.payload);
        }
      });
    setCascadingFailures(Array.from(cascadesMap.values()).slice(0, 10));
  }, [events]);

  useEffect(() => {
    // Fetch remediation actions
    api
      .fetch("GET", "/api/v1/demo/remediation/actions")
      .then((data: any) => {
        setRemediationActions(data.executed_actions || []);
      })
      .catch(() => {});
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-3xl font-bold">Incident Command Center</h1>
        <div className="flex gap-4">
          <HealthScoreCard score={healthScore} />
          <button
            onClick={() => (window.location.href = "/demo/scenarios")}
            className="px-4 py-2 bg-sentinel-accent text-sentinel-900 rounded font-bold hover:opacity-90"
          >
            Trigger Scenario
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">
          <IncidentFeed incidents={incidents} />
          <RCATimelinePanel insights={aiInsights} />
          <CascadingFailureMap failures={cascadingFailures} />
        </div>

        <div className="space-y-6">
          <ActiveIncidentsPanel incidents={incidents} />
          <RemediationActionsPanel actions={remediationActions} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <AIReasoningStream insights={aiInsights} />
        <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-sentinel-accent mb-4">Live Recommendations</h3>
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {recommendations.map((rec, idx) => (
              <div key={idx} className="bg-sentinel-800/50 p-2 rounded text-xs border-l-2 border-sentinel-500">
                <p className="font-semibold text-gray-200">{rec.title}</p>
                <p className="text-gray-400 text-[10px]">Priority: {rec.priority}</p>
              </div>
            ))}
            {recommendations.length === 0 && <p className="text-gray-500 text-xs">Awaiting recommendations...</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
