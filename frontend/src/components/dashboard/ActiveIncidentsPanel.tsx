interface Props {
  incidents: any[];
}

export default function ActiveIncidentsPanel({ incidents }: Props) {
  const criticalCount = incidents.filter((i) => i.severity === "critical").length;
  const errorCount = incidents.filter((i) => i.severity === "error").length;
  const warningCount = incidents.filter((i) => i.severity === "warning").length;

  return (
    <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4 space-y-3">
      <h3 className="text-sm font-semibold text-sentinel-accent">Active Incidents</h3>

      <div className="space-y-2">
        <div className="flex items-center justify-between p-2 bg-sentinel-800/50 rounded">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
            <span className="text-xs text-gray-300">Critical</span>
          </div>
          <span className="text-sm font-bold text-red-400">{criticalCount}</span>
        </div>

        <div className="flex items-center justify-between p-2 bg-sentinel-800/50 rounded">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-orange-500 rounded-full" />
            <span className="text-xs text-gray-300">Error</span>
          </div>
          <span className="text-sm font-bold text-orange-400">{errorCount}</span>
        </div>

        <div className="flex items-center justify-between p-2 bg-sentinel-800/50 rounded">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-yellow-500 rounded-full" />
            <span className="text-xs text-gray-300">Warning</span>
          </div>
          <span className="text-sm font-bold text-yellow-400">{warningCount}</span>
        </div>
      </div>

      <div className="text-xs text-gray-500 text-center pt-2 border-t border-sentinel-700">
        Total: {incidents.length} incidents
      </div>
    </div>
  );
}
