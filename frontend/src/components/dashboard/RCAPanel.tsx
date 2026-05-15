interface RCAData {
  root_cause?: string;
  root_service?: string;
  confidence?: number;
  cascade_chain?: Array<{ service: string; order: number; failure_mode?: string; influence?: number }>;
  affected_count?: number;
  propagation_depth?: number;
}

interface Props {
  rca: RCAData | null;
  rawEvents?: any[];
}

export default function RCAPanel({ rca, rawEvents }: Props) {
  if (!rca) {
    return (
      <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-sentinel-accent mb-2">Root Cause Analysis</h3>
        <p className="text-gray-500 text-xs">Select an incident to view RCA</p>
      </div>
    );
  }

  const confidence = (rca.confidence ?? 0) * 100;
  const cascade = rca.cascade_chain ?? [];
  const confidenceColor =
    confidence >= 80 ? "text-green-400" : confidence >= 60 ? "text-yellow-400" : "text-red-400";

  return (
    <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4 space-y-3">
      <div className="flex items-start justify-between">
        <h3 className="text-sm font-semibold text-sentinel-accent">Root Cause Analysis</h3>
        <span className={`text-xs font-bold ${confidenceColor}`}>{confidence.toFixed(0)}%</span>
      </div>

      {rca.root_cause && (
        <div className="bg-sentinel-800/50 rounded p-2 border-l-2 border-sentinel-500">
          <p className="text-xs font-semibold text-gray-300 mb-1">Primary Cause</p>
          <p className="text-xs text-gray-400">{rca.root_cause}</p>
        </div>
      )}

      {rca.root_service && (
        <div className="text-xs">
          <span className="text-gray-500">Service: </span>
          <span className="text-sentinel-accent font-medium">{rca.root_service}</span>
        </div>
      )}

      {cascade.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-gray-300">Cascade Chain ({cascade.length})</p>
          <ol className="space-y-1 border-l border-sentinel-700/50 pl-3">
            {cascade.map((c, i) => (
              <li key={i} className="text-xs text-gray-400 flex items-center justify-between">
                <span>
                  <span className="text-sentinel-accent font-bold mr-2">{c.order}.</span>
                  {c.service}
                  {c.failure_mode && <span className="text-gray-600 ml-2">({c.failure_mode})</span>}
                </span>
                {c.influence && (
                  <span className="text-[10px] text-orange-400">{(c.influence * 100).toFixed(0)}%</span>
                )}
              </li>
            ))}
          </ol>
        </div>
      )}

      {(rca.affected_count || rca.propagation_depth) && (
        <div className="grid grid-cols-2 gap-2 pt-2 border-t border-sentinel-700/30 text-[10px]">
          {rca.affected_count && (
            <div className="text-gray-400">
              <span className="text-gray-600">Services Affected:</span> {rca.affected_count}
            </div>
          )}
          {rca.propagation_depth && (
            <div className="text-gray-400">
              <span className="text-gray-600">Depth:</span> {rca.propagation_depth}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
