interface Props {
  insights: any[];
}

export default function RCATimelinePanel({ insights }: Props) {
  const rcaInsights = insights.filter((i) => i.agent === "rca").slice(0, 5);

  return (
    <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-sentinel-accent mb-4">RCA Timeline</h3>
      <div className="space-y-2 border-l-2 border-sentinel-700 pl-4">
        {rcaInsights.map((insight, idx) => (
          <div key={idx} className="relative">
            <div className="absolute -left-6 w-3 h-3 bg-sentinel-accent rounded-full" />
            <div className="bg-sentinel-800/30 p-2 rounded">
              <p className="text-xs text-gray-300 font-semibold">Root Cause Found</p>
              {insight.findings && insight.findings.length > 0 && (
                <p className="text-[10px] text-gray-400 mt-1">{insight.findings[0]}</p>
              )}
              <p className="text-[10px] text-sentinel-accent mt-1">Confidence: {(insight.confidence * 100).toFixed(0)}%</p>
            </div>
          </div>
        ))}
        {rcaInsights.length === 0 && (
          <p className="text-gray-500 text-xs">RCA analysis pending...</p>
        )}
      </div>
    </div>
  );
}
