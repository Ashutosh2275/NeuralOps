interface Props {
  score: number;
}

export default function HealthScoreCard({ score }: Props) {
  let color = "text-red-400";
  let bgColor = "bg-red-900/20";
  let borderColor = "border-red-500";

  if (score >= 80) {
    color = "text-green-400";
    bgColor = "bg-green-900/20";
    borderColor = "border-green-500";
  } else if (score >= 60) {
    color = "text-yellow-400";
    bgColor = "bg-yellow-900/20";
    borderColor = "border-yellow-500";
  } else if (score >= 40) {
    color = "text-orange-400";
    bgColor = "bg-orange-900/20";
    borderColor = "border-orange-500";
  }

  return (
    <div className={`${bgColor} border ${borderColor} rounded-lg p-4 min-w-[180px]`}>
      <p className="text-xs text-gray-400 mb-1">Infrastructure Health</p>
      <div className="flex items-baseline gap-2">
        <span className={`text-3xl font-bold ${color}`}>{score.toFixed(0)}</span>
        <span className="text-xs text-gray-500">%</span>
      </div>
      <div className="w-full bg-sentinel-800 rounded h-1 mt-2">
        <div
          className={`h-full rounded transition-all duration-300 ${
            score >= 80
              ? "bg-green-600"
              : score >= 60
                ? "bg-yellow-600"
                : score >= 40
                  ? "bg-orange-600"
                  : "bg-red-600"
          }`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}
