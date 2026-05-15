import type { WSEvent } from "../../hooks/useWebSocket";

interface AIInsight {
  agent: string;
  findings: string[];
  confidence: number;
  reasoning: string;
}

interface Props {
  insights: AIInsight[];
  wsEvents: WSEvent[];
}

function ConfidenceBar({ value }: { value: number }) {
  let bgColor = "bg-red-600";
  if (value >= 0.8) bgColor = "bg-green-600";
  else if (value >= 0.6) bgColor = "bg-yellow-600";
  else if (value >= 0.4) bgColor = "bg-orange-600";

  return (
    <div className="w-full bg-sentinel-800 rounded h-1.5">
      <div className={`${bgColor} h-full rounded`} style={{ width: `${value * 100}%` }} />
    </div>
  );
}

export default function AIInsightsPanel({ insights, wsEvents }: Props) {
  const aiEvents = wsEvents.filter((e) => e.type === "ai_insight").slice(0, 10);
  const allInsights = insights.concat(
    aiEvents.map((e: any) => ({
      agent: e.payload?.agent || "unknown",
      findings: e.payload?.findings || [],
      confidence: e.payload?.confidence || 0,
      reasoning: e.payload?.reasoning || "",
    }))
  );

  const agentColors: Record<string, string> = {
    cpu: "text-red-400",
    memory: "text-orange-400",
    storage: "text-blue-400",
    network: "text-purple-400",
    logs: "text-cyan-400",
    rca: "text-green-400",
    npl_assistant: "text-pink-400",
    correlation: "text-yellow-400",
    recommendation: "text-indigo-400",
    summarization: "text-violet-400",
  };

  return (
    <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4 space-y-4">
      <h3 className="text-sm font-semibold text-sentinel-accent">AI Analysis</h3>
      {allInsights.slice(0, 5).map((insight, idx) => (
        <div key={idx} className="bg-sentinel-800/50 border border-sentinel-700/50 rounded p-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className={`text-xs font-semibold ${agentColors[insight.agent] || "text-gray-400"}`}>
              {insight.agent.toUpperCase()}
            </span>
            <span className="text-xs text-gray-500">{(insight.confidence * 100).toFixed(0)}%</span>
          </div>
          <ConfidenceBar value={insight.confidence} />
          {insight.findings && insight.findings.length > 0 && (
            <p className="text-xs text-gray-300 line-clamp-2">{insight.findings[0]}</p>
          )}
          {insight.reasoning && (
            <p className="text-[10px] text-gray-500 italic">{insight.reasoning.slice(0, 80)}</p>
          )}
        </div>
      ))}
      {allInsights.length === 0 && (
        <p className="text-gray-500 text-xs">Awaiting AI analysis...</p>
      )}
    </div>
  );
}
