import { Link, useLocation } from "react-router-dom";
import { useWebSocket } from "../../hooks/useWebSocket";

const NAV = [
  { path: "/", label: "Dashboard" },
  { path: "/incidents", label: "Incidents" },
  { path: "/topology", label: "Topology" },
  { path: "/nlp", label: "AI Assistant" },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const { connected } = useWebSocket();

  return (
    <div className="min-h-screen flex">
      <aside className="w-56 bg-sentinel-900 border-r border-sentinel-700 flex flex-col">
        <div className="p-4 border-b border-sentinel-700">
          <h1 className="font-display text-lg font-bold text-sentinel-accent">SentinelOps AI</h1>
          <p className="text-xs text-gray-500 mt-1">Operational Intelligence</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {NAV.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`block px-3 py-2 rounded text-sm ${
                location.pathname === item.path
                  ? "bg-sentinel-700 text-sentinel-accent"
                  : "text-gray-400 hover:bg-sentinel-800"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="p-3 border-t border-sentinel-700 text-xs">
          <span className={`inline-block w-2 h-2 rounded-full mr-2 ${connected ? "bg-sentinel-success" : "bg-sentinel-danger"}`} />
          {connected ? "Live" : "Disconnected"}
        </div>
      </aside>
      <main className="flex-1 overflow-auto p-6">{children}</main>
    </div>
  );
}
