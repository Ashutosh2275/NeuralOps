interface AgentConfidence {
  agent: string;
  confidence: number;
  success: boolean;
}

interface Props {
  confidences: AgentConfidence[];
  title?: string;
}

export default function ConfidenceVisualization({ confidences, title = "Agent Confidence" }: Props) {
  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.85) return "bg-green-600";
    if (confidence >= 0.7) return "bg-emerald-600";
    if (confidence >= 0.55) return "bg-yellow-600";
    if (confidence >= 0.4) return "bg-orange-600";
    return "bg-red-600";
  };

  const getTextColor = (confidence: number): string => {
    if (confidence >= 0.85) return "text-green-400";
    if (confidence >= 0.7) return "text-emerald-400";
    if (confidence >= 0.55) return "text-yellow-400";
    if (confidence >= 0.4) return "text-orange-400";
    return "text-red-400";
  };

  const avgConfidence =
    confidences.length > 0
      ? confidences.reduce((sum, c) => sum + c.confidence, 0) / confidences.length
      : 0;

  const sortedByConfidence = [...confidences].sort((a, b) => b.confidence - a.confidence);

  return (
    <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-sentinel-accent">{title}</h3>
        <span className={`text-sm font-bold ${getTextColor(avgConfidence)}`}>
          {(avgConfidence * 100).toFixed(0)}%
        </span>
      </div>

      <div className="w-full bg-sentinel-800 rounded h-2">
        <div
          className={`${getConfidenceColor(avgConfidence)} h-full rounded transition-all duration-300`}
          style={{ width: `${avgConfidence * 100}%` }}
        />
      </div>

      <div className="space-y-2">
        {sortedByConfidence.map((item) => (
          <div key={item.agent} className="flex items-center gap-2">
            <span className="text-xs font-semibold text-gray-400 w-24 truncate">{item.agent}</span>
            <div className="flex-1 h-1.5 bg-sentinel-800 rounded overflow-hidden">
              <div
                className={`${getConfidenceColor(item.confidence)} h-full transition-all duration-300`}
                style={{ width: `${item.confidence * 100}%` }}
              />
            </div>
            <span className={`text-xs font-bold w-12 text-right ${getTextColor(item.confidence)}`}>
              {(item.confidence * 100).toFixed(0)}%
            </span>
            {!item.success && <span className="text-[10px] text-red-400">✕</span>}
          </div>
        ))}
      </div>

      {confidences.length === 0 && (
        <p className="text-gray-500 text-xs text-center py-2">No agent data available</p>
      )}
    </div>
  );
}
