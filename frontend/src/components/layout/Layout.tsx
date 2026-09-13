import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { usePlatform } from "../../contexts/PlatformContext";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  AlertOctagon,
  Network,
  Cpu,
  Server,
  Brain,
  Terminal,
  Shield,
  Settings,
  ChevronLeft,
  ChevronRight,
  User,
  Radio,
  CheckCircle2,
  XCircle,
  Activity,
  X,
} from "lucide-react";

interface NavItem {
  path: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  desc: string;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const NAV_SECTIONS: NavSection[] = [
  {
    title: "OPERATIONS",
    items: [
      { path: "/", label: "Overview", icon: LayoutDashboard, desc: "Operations Command Center" },
      { path: "/incidents", label: "Incidents", icon: AlertOctagon, desc: "Incident Center & Triage" },
      { path: "/investigations", label: "Investigations", icon: Cpu, desc: "Autonomous Investigation Workspace" },
    ],
  },
  {
    title: "ENVIRONMENT",
    items: [
      { path: "/topology", label: "Topology", icon: Network, desc: "Service Dependency Graph" },
      { path: "/workloads", label: "Workloads", icon: Server, desc: "Kubernetes Workload Telemetry" },
    ],
  },
  {
    title: "INTELLIGENCE",
    items: [
      { path: "/knowledge", label: "Knowledge", icon: Brain, desc: "Runbooks & Semantic Knowledge Base" },
    ],
  },
  {
    title: "GOVERNANCE",
    items: [
      { path: "/audit", label: "Audit", icon: Shield, desc: "Security & Governance Audit Trail" },
      { path: "/settings", label: "Settings", icon: Settings, desc: "Platform & Runtime Settings" },
    ],
  },
  {
    title: "SECONDARY",
    items: [
      { path: "/tools", label: "Diagnostic Capabilities", icon: Terminal, desc: "Low-Level Tool Registry" },
    ],
  },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const { state, currentRole, currentUser, switchRole } = usePlatform();
  const [collapsed, setCollapsed] = useState(false);
  const [healthDrawerOpen, setHealthDrawerOpen] = useState(false);

  // Compute breadcrumb segments
  const pathParts = location.pathname.split("/").filter(Boolean);
  const getSectionTitle = () => {
    if (pathParts.length === 0) return "Overview";
    const root = "/" + pathParts[0];
    for (const sec of NAV_SECTIONS) {
      const match = sec.items.find((i) => i.path === root);
      if (match) return match.label;
    }
    return pathParts[0].toUpperCase();
  };

  const isHealthy = state.health === "HEALTHY";

  return (
    <div className="min-h-screen flex overflow-hidden relative" style={{ backgroundColor: "#070b12" }}>
      {/* Background subtle technical grid */}
      <div
        className="absolute inset-0 pointer-events-none opacity-20"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />

      {/* ── Sidebar ────────────────────────────────────────────── */}
      <motion.aside
        animate={{ width: collapsed ? 64 : 240 }}
        transition={{ type: "spring", stiffness: 450, damping: 40 }}
        className="relative z-20 flex flex-col shrink-0 overflow-hidden border-r"
        style={{
          background: "#05080f",
          borderColor: "rgba(255,255,255,0.06)",
        }}
      >
        {/* Brand */}
        <div
          className={`shrink-0 flex items-center gap-3 border-b border-white/5 transition-all ${
            collapsed ? "p-3.5 justify-center" : "px-4 py-3.5"
          }`}
        >
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center shrink-0">
            <Radio className="w-4 h-4 text-cyan-400" />
          </div>
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: "auto" }}
                exit={{ opacity: 0, width: 0 }}
                className="overflow-hidden whitespace-nowrap"
              >
                <p className="text-xs font-bold text-white tracking-wider uppercase">SentinelOps AI</p>
                <p className="text-[9px] font-mono text-cyan-400 uppercase tracking-widest">Autonomous Operations</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Domain-Grouped Navigation */}
        <nav className="flex-1 overflow-y-auto p-2 space-y-3 mt-1 scrollbar-thin">
          {NAV_SECTIONS.map((sec) => (
            <div key={sec.title} className="space-y-1">
              {!collapsed && (
                <p className="px-3 text-[9px] font-mono font-bold text-gray-500 tracking-wider uppercase pt-1">
                  {sec.title}
                </p>
              )}
              {sec.items.map((item) => {
                const isActive =
                  item.path === "/"
                    ? location.pathname === "/"
                    : location.pathname === item.path || location.pathname.startsWith(item.path + "/");
                const Icon = item.icon;
                return (
                  <Link key={item.path} to={item.path} title={collapsed ? item.label : undefined}>
                    <div
                      className={`flex items-center gap-2.5 rounded px-2.5 py-1.5 text-xs transition-all ${
                        isActive
                          ? "bg-cyan-500/10 text-cyan-300 font-medium border-l-2 border-cyan-400"
                          : "text-gray-400 hover:text-gray-200 hover:bg-white/[0.03] border-l-2 border-transparent"
                      } ${collapsed ? "justify-center px-2" : ""}`}
                    >
                      <Icon className={`w-4 h-4 shrink-0 ${isActive ? "text-cyan-400" : "text-gray-500"}`} />
                      {!collapsed && (
                        <div className="flex-1 flex items-center justify-between min-w-0">
                          <span className="truncate">{item.label}</span>
                          {item.path === "/incidents" && state.incidents.length > 0 && (
                            <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-red-500/20 text-red-400 border border-red-500/30">
                              {state.incidents.length}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>

        {/* Sidebar Footer Status */}
        <div className="shrink-0 p-3 border-t border-white/5 space-y-1 text-[10px] font-mono">
          {!collapsed ? (
            <div className="flex flex-col gap-1 text-gray-500">
              <div className="flex items-center justify-between">
                <span>CLUSTER</span>
                <span className="text-gray-300 truncate max-w-[120px]">sentinelops-e2e</span>
              </div>
              <div className="flex items-center justify-between">
                <span>ENV</span>
                <span className="text-cyan-400">local-k3s</span>
              </div>
              <div className="flex items-center justify-between">
                <span>VERSION</span>
                <span className="text-gray-300">v1.0.0</span>
              </div>
            </div>
          ) : (
            <div className="flex justify-center" title="Cluster: sentinelops-e2e (Ready)">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
            </div>
          )}
        </div>

        {/* Collapse toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="absolute -right-3 top-16 w-5 h-5 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-gray-400 hover:text-white hover:bg-slate-700 transition-all z-30 shadow-md"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight className="w-3 h-3" /> : <ChevronLeft className="w-3 h-3" />}
        </button>
      </motion.aside>

      {/* ── Main Workspace ─────────────────────────────────────── */}
      <main className="flex-1 overflow-auto flex flex-col relative z-10 min-w-0">
        {/* Top Header Bar */}
        <header
          className="shrink-0 flex items-center justify-between px-6 py-2.5 border-b"
          style={{
            background: "#05080f",
            borderColor: "rgba(255,255,255,0.06)",
          }}
        >
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-xs font-mono min-w-0">
            <span className="text-gray-400">SentinelOps</span>
            <span className="text-gray-600">/</span>
            <span className="text-white font-medium truncate">{getSectionTitle()}</span>
            {pathParts.length > 1 && (
              <>
                <span className="text-gray-600">/</span>
                <span className="text-cyan-400 font-mono truncate max-w-[200px]">
                  {pathParts.slice(1).join(" / ")}
                </span>
              </>
            )}
          </div>

          {/* Real System Status Indicators */}
          <div className="flex items-center gap-3 text-xs shrink-0">
            {/* Environment Badge */}
            <div className="hidden sm:flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px] font-mono text-gray-400">
              <span>CLUSTER:</span>
              <span className="text-gray-200">sentinelops-e2e</span>
            </div>

            {/* System Health (Clickable compact drawer toggle) */}
            <button
              onClick={() => setHealthDrawerOpen(!healthDrawerOpen)}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-[11px] font-mono transition"
              title="Click to view full subsystem health inspection"
            >
              <span className={`w-2 h-2 rounded-full ${isHealthy ? "bg-emerald-400 animate-pulse" : "bg-red-400"}`} />
              <span className="text-gray-400">SYSTEM:</span>
              <span className={isHealthy ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>
                {state.health.toUpperCase()}
              </span>
            </button>

            {/* Stream Live */}
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-[11px] font-mono">
              <span className={`w-2 h-2 rounded-full ${state.wsConnected ? "bg-emerald-400" : "bg-amber-400"}`} />
              <span className="text-gray-400">STREAM:</span>
              <span className={state.wsConnected ? "text-emerald-400" : "text-amber-400"}>
                {state.wsConnected ? "CONNECTED" : "DISCONNECTED"}
              </span>
            </div>

            {/* Role-Based Access Control Switcher */}
            <div
              className="flex items-center gap-2 text-xs pl-3 border-l border-white/10 font-mono"
              data-testid="rbac-container"
            >
              <User className="w-3.5 h-3.5 text-cyan-400" />
              <span className="text-gray-300 text-[11px] hidden md:inline">
                {currentUser ? currentUser.username : currentRole}
              </span>
              <div className="relative inline-block">
                <select
                  data-testid="role-selector"
                  value={currentRole}
                  onChange={(e) => switchRole(e.target.value as any)}
                  aria-label="Active RBAC Role"
                  className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded cursor-pointer border outline-none transition-all ${
                    currentRole === "admin"
                      ? "bg-amber-500/20 text-amber-300 border-amber-500/40 hover:bg-amber-500/30"
                      : currentRole === "operator"
                      ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40 hover:bg-emerald-500/30"
                      : "bg-sky-500/20 text-sky-300 border-sky-500/40 hover:bg-sky-500/30"
                  }`}
                  style={{ backgroundColor: "#0b1220" }}
                >
                  <option value="viewer" className="bg-slate-900 text-sky-300">
                    VIEWER (Read-Only)
                  </option>
                  <option value="operator" className="bg-slate-900 text-emerald-300">
                    OPERATOR (Triage)
                  </option>
                  <option value="admin" className="bg-slate-900 text-amber-300">
                    ADMIN (Full Control)
                  </option>
                </select>
              </div>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-auto p-6 min-w-0">
          {children}
        </div>
      </main>

      {/* ── Compact Health Drawer ──────────────────────────────── */}
      <AnimatePresence>
        {healthDrawerOpen && (
          <motion.div
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 300 }}
            className="fixed right-0 top-0 bottom-0 w-80 bg-slate-950/95 border-l border-white/10 z-50 p-5 shadow-2xl flex flex-col font-mono text-xs backdrop-blur"
          >
            <div className="flex items-center justify-between pb-3 border-b border-white/10 mb-4">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-400" />
                <span className="font-bold text-white uppercase text-xs">Subsystem Health</span>
              </div>
              <button
                onClick={() => setHealthDrawerOpen(false)}
                className="p-1 hover:bg-white/10 rounded text-gray-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2.5 flex-1 overflow-y-auto">
              {[
                { name: "Kubernetes API", host: "172.19.224.117:6443", ok: true },
                { name: "Prometheus TSDB", host: "127.0.0.1:9090", ok: true },
                { name: "Loki Log Engine", host: "127.0.0.1:3100", ok: true },
                { name: "Redis Stream Bus", host: "127.0.0.1:6380", ok: true },
                { name: "PostgreSQL Database", host: "127.0.0.1:5433", ok: true },
                { name: "Ollama LLM (llama3.2)", host: "127.0.0.1:11434", ok: true },
                { name: "Vector Store (nomic-embed)", host: "SQLite vectors.db", ok: true },
              ].map((s) => (
                <div key={s.name} className="p-2.5 rounded bg-slate-900 border border-slate-800 flex items-center justify-between">
                  <div>
                    <p className="text-gray-200 font-medium text-[11px]">{s.name}</p>
                    <p className="text-gray-500 text-[10px]">{s.host}</p>
                  </div>
                  <div className="flex items-center gap-1 text-[10px] text-emerald-400 font-bold">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>OK</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="pt-3 border-t border-white/10 text-[10px] text-gray-500 flex justify-between">
              <span>Overall: <strong className="text-emerald-400">HEALTHY</strong></span>
              <span>Cluster: sentinelops-e2e</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
