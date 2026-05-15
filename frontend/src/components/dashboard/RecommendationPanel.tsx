import type { Recommendation } from "../../lib/api";

export default function RecommendationPanel({ items }: { items: Recommendation[] }) {
  return (
    <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4">
      <h3 className="text-sm font-semibold mb-3">Recommendations</h3>
      <ul className="space-y-2">
        {items.map((r) => (
          <li key={r.id} className="text-xs border border-sentinel-700 rounded p-2">
            <div className="flex justify-between">
              <span className="font-medium text-gray-200">{r.title}</span>
              <span className="text-sentinel-accent">P{r.priority}</span>
            </div>
            <p className="text-gray-500 mt-1">{r.description}</p>
            {r.kubectl_command && (
              <code className="block mt-1 text-sentinel-accent bg-sentinel-950 p-1 rounded text-[10px]">
                {r.kubectl_command}
              </code>
            )}
          </li>
        ))}
        {items.length === 0 && <p className="text-gray-500">No recommendations yet</p>}
      </ul>
    </div>
  );
}
