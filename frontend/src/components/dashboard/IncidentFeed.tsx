interface Props {
  incidents: any[];
}

export default function IncidentFeed({ incidents }: Props) {
  return (
    <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-sentinel-accent mb-4">Live Incident Feed</h3>
      <div className="space-y-2 max-h-[500px] overflow-y-auto">
        {incidents.map((incident, idx) => (
          <div
            key={idx}
            className={`p-3 rounded border-l-4 ${
              incident.severity === "critical"
                ? "bg-red-900/20 border-red-500"
                : incident.severity === "error"
                  ? "bg-orange-900/20 border-orange-500"
                  : "bg-yellow-900/20 border-yellow-500"
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-gray-100">{incident.title || "Incident"}</p>
                <p className="text-[10px] text-gray-400">{incident.namespace}</p>
              </div>
              <span className={`text-[10px] font-bold px-2 py-1 rounded ${
                incident.severity === "critical"
                  ? "bg-red-600"
                  : incident.severity === "error"
                    ? "bg-orange-600"
                    : "bg-yellow-600"
              }`}>
                {incident.severity?.toUpperCase()}
              </span>
            </div>
          </div>
        ))}
        {incidents.length === 0 && <p className="text-gray-500 text-xs text-center py-4">No incidents detected</p>}
      </div>
    </div>
  );
}
