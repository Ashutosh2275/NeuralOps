interface CascadeChainItem {
  service: string;
  order: number;
  failure_mode: string;
  influence: number;
}

interface CascadingFailureVisualizerProps {
  chain: CascadeChainItem[];
  affectedCount: number;
  propagationDepth: number;
  escalationFactor: number;
}

export default function CascadingFailureVisualizer({
  chain,
  affectedCount,
  propagationDepth,
  escalationFactor,
}: CascadingFailureVisualizerProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-2">
        <div className="bg-red-900/20 border border-red-700 rounded p-3">
          <p className="text-xs text-gray-400">Affected Services</p>
          <p className="text-2xl font-bold text-red-400">{affectedCount}</p>
        </div>
        <div className="bg-orange-900/20 border border-orange-700 rounded p-3">
          <p className="text-xs text-gray-400">Propagation Depth</p>
          <p className="text-2xl font-bold text-orange-400">{propagationDepth}</p>
        </div>
        <div className="bg-yellow-900/20 border border-yellow-700 rounded p-3">
          <p className="text-xs text-gray-400">Escalation Factor</p>
          <p className="text-2xl font-bold text-yellow-400">{escalationFactor.toFixed(2)}x</p>
        </div>
        <div className="bg-purple-900/20 border border-purple-700 rounded p-3">
          <p className="text-xs text-gray-400">Chain Length</p>
          <p className="text-2xl font-bold text-purple-400">{chain.length}</p>
        </div>
      </div>

      <div className="bg-sentinel-900 border border-sentinel-700 rounded p-4">
        <h3 className="text-sm font-semibold mb-3">Cascade Path</h3>
        <div className="space-y-2">
          {chain.map((item, i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-sentinel-700 flex items-center justify-center text-xs font-bold">
                {item.order}
              </div>
              <div className="flex-grow">
                <p className="text-sm font-medium">{item.service}</p>
                <p className="text-xs text-gray-400">{item.failure_mode}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-400">Influence</p>
                <p className="text-sm font-semibold">{(item.influence * 100).toFixed(0)}%</p>
              </div>
              {i < chain.length - 1 && (
                <div className="text-center text-red-400">↓</div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
