import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, IncidentSummary } from "../lib/api";

export default function Incidents() {
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.incidents()
      .then(setIncidents)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-500">Loading incidents...</p>;

  return (
    <div className="space-y-4">
      <h2 className="font-display text-2xl font-bold">Incidents</h2>
      <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-sentinel-800 text-gray-400">
            <tr>
              <th className="text-left p-3">Title</th>
              <th className="text-left p-3">Status</th>
              <th className="text-left p-3">Severity</th>
              <th className="text-left p-3">Service</th>
              <th className="text-left p-3">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {incidents.map((i) => (
              <tr key={i.id} className="border-t border-sentinel-700 hover:bg-sentinel-800">
                <td className="p-3">
                  <Link to={`/incidents/${i.id}`} className="text-sentinel-accent hover:underline">
                    {i.title}
                  </Link>
                </td>
                <td className="p-3">{i.status}</td>
                <td className="p-3">
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    i.severity === "critical" ? "bg-red-900" : "bg-yellow-900"
                  }`}>{i.severity}</span>
                </td>
                <td className="p-3">{i.root_service ?? "—"}</td>
                <td className="p-3">{i.confidence_score != null ? `${(i.confidence_score * 100).toFixed(0)}%` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {incidents.length === 0 && (
          <p className="p-6 text-gray-500 text-center">No incidents yet. Start workers to begin detection.</p>
        )}
      </div>
    </div>
  );
}
