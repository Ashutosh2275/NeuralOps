interface Props {
  failures: any[];
}

export default function CascadingFailureMap({ failures }: Props) {
  return (
    <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-sentinel-accent mb-4">Cascading Failure Map</h3>
      <div className="space-y-2 max-h-[300px] overflow-y-auto">
        {failures.map((failure, idx) => (
          <div key={idx} className="bg-sentinel-800/50 p-2 rounded border-l-2 border-red-500">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-xs font-bold text-gray-200">{failure.origin_node || "Service"}</p>
                <p className="text-[10px] text-gray-400">
                  {failure.affected_count || 0} services affected
                </p>
              </div>
              <span className="text-[10px] text-red-400 font-bold">
                Depth: {failure.propagation_depth || 0}
              </span>
            </div>
          </div>
        ))}
        {failures.length === 0 && (
          <p className="text-gray-500 text-xs text-center py-4">No cascading failures detected</p>
        )}
      </div>
    </div>
  );
}
