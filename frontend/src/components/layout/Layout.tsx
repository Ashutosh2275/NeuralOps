import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { useWebSocket } from "../../hooks/useWebSocket";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard, AlertOctagon, Network, Cpu, Terminal,
  ActivitySquare, ChevronLeft, ChevronRight, Radio, ShieldCheck,
  Brain, BarChart3, Clapperboard, Shield, Settings, Zap
} from "lucide-react";

// ── Nav groups ─────────────────────────────────────────────────
const NAV_GROUPS = [
  {
    label: "Core",
    items: [
      { path: "/",               label: "Operations",   icon: LayoutDashboard, desc: "Global overview",       accent: "cyan"   },
      { path: "/incident-command",label:"AI War Room",  icon: ActivitySquare,  desc: "Live incident AI",      accent: "red"    },
      { path: "/command-center", label: "War Room",     icon: Terminal,        desc: "Enterprise command",    accent: "orange" },
    ],
  },
  {
    label: "Intelligence",
    items: [
      { path: "/incidents",      label: "Incidents",    icon: AlertOctagon,    desc: "Active anomalies",      accent: "red"    },
      { path: "/topology",       label: "Neural Map",   icon: Network,         desc: "Dependency graph",      accent: "cyan"   },
      { path: "/ai-agents",      label: "AI Agents",    icon: Brain,           desc: "Orchestration network",  accent: "purple" },
      { path: "/nlp",            label: "AI Oracle",    icon: Cpu,             desc: "NLP assistant",         accent: "purple" },
    ],
  },
  {
    label: "Insights",
    items: [
      { path: "/analytics",      label: "Analytics",    icon: BarChart3,       desc: "Infra trends",          accent: "cyan"   },
      { path: "/security",       label: "Security",     icon: Shield,          desc: "Resilience status",     accent: "green"  },
    ],
  },
  {
    label: "Platform",
    items: [
      { path: "/demo",           label: "Demo Center",  icon: Clapperboard,    desc: "Chaos & presentation",  accent: "yellow" },
      { path: "/settings",       label: "Settings",     icon: Settings,        desc: "Platform config",       accent: "gray"   },
    ],
  },
];

const ACCENT_COLORS: Record<string, string> = {
  cyan:   "text-cyan-400",
  red:    "text-red-400",
  orange: "text-orange-400",
  purple: "text-purple-400",
  green:  "text-green-400",
  yellow: "text-yellow-400",
  gray:   "text-gray-400",
};

const pageVariants = {
  initial: { opacity: 0, y: 14, filter: "blur(4px)" },
  animate: { opacity: 1, y: 0,  filter: "blur(0px)" },
  exit:    { opacity: 0, y: -8, filter: "blur(2px)" },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const { connected, events } = useWebSocket();
  const [collapsed, setCollapsed] = useState(false);
  const [time, setTime] = useState(new Date());
  const [activityFlash, setActivityFlash] = useState(false);
  const [incidentCount, setIncidentCount] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    if (!events.length) return;
    setActivityFlash(true);
    setTimeout(() => setActivityFlash(false), 1200);
    // Count anomaly events
    if (events[0]?.type === "anomaly") setIncidentCount(c => c + 1);
  }, [events.length]);

  const currentNav = NAV_GROUPS.flatMap(g => g.items).find(n => n.path === location.pathname);

  return (
    <div className="min-h-screen flex bg-sentinel-950 overflow-hidden relative">
      {/* Ambient backgrounds */}
      <div className="absolute inset-0 cyber-grid opacity-100 pointer-events-none" />
      <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(ellipse_90%_55%_at_50%_0%,rgba(34,211,238,0.055),transparent)]" />
      <div className="scanlines absolute inset-0 z-50 pointer-events-none opacity-25" />

      {/* ── Sidebar ────────────────────────────────────────────── */}
      <motion.aside
        animate={{ width: collapsed ? 68 : 248 }}
        transition={{ type: "spring", stiffness: 400, damping: 36 }}
        className="relative z-20 flex flex-col shrink-0 overflow-hidden"
        style={{
          background: "linear-gradient(180deg, rgba(9,17,30,0.98) 0%, rgba(5,10,20,0.98) 100%)",
          borderRight: "1px solid rgba(34,211,238,0.1)",
          boxShadow: "4px 0 40px rgba(0,0,0,0.6)",
        }}
      >
        {/* Brand */}
        <div className={`shrink-0 flex items-center gap-3 border-b border-white/5 transition-all ${collapsed ? "p-4 justify-center" : "p-5"}`}>
          <div className="w-9 h-9 rounded-xl bg-sentinel-accent/15 border border-sentinel-accent/40 flex items-center justify-center shrink-0 glow-border-accent">
            <Network className="w-5 h-5 text-sentinel-accent" />
          </div>
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: "auto" }}
                exit={{ opacity: 0, width: 0 }}
                className="overflow-hidden whitespace-nowrap"
              >
                <p className="text-sm font-display font-black text-white tracking-wider uppercase glow-text-accent">NeuralOps</p>
                <p className="text-[8px] font-mono text-gray-600 uppercase tracking-[0.2em]">AI Infrastructure OS</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto p-2 space-y-4 mt-2">
          {NAV_GROUPS.map((group) => (
            <div key={group.label}>
              <AnimatePresence>
                {!collapsed && (
                  <motion.p
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    className="text-[8px] font-mono text-gray-700 uppercase tracking-[0.2em] px-3 mb-1"
                  >
                    {group.label}
                  </motion.p>
                )}
              </AnimatePresence>
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const isActive = location.pathname === item.path;
                  const Icon = item.icon;
                  const accentColor = ACCENT_COLORS[item.accent];
                  return (
                    <Link key={item.path} to={item.path}>
                      <motion.div
                        whileHover={{ x: collapsed ? 0 : 3 }}
                        whileTap={{ scale: 0.97 }}
                        className={`relative flex items-center gap-3 rounded-lg transition-all duration-200 ${
                          collapsed ? "justify-center px-2 py-2.5" : "px-3 py-2.5"
                        } ${isActive
                          ? "bg-white/5 border-l-2 border-sentinel-accent"
                          : "hover:bg-white/4 border-l-2 border-transparent"
                        }`}
                      >
                        {isActive && (
                          <motion.div
                            layoutId="sidebarGlow"
                            className="absolute inset-0 rounded-lg"
                            style={{ background: "rgba(34,211,238,0.04)" }}
                            transition={{ type: "spring", stiffness: 500, damping: 35 }}
                          />
                        )}
                        <Icon className={`w-4 h-4 shrink-0 z-10 transition-all ${isActive ? "text-sentinel-accent drop-shadow-[0_0_5px_rgba(34,211,238,0.9)]" : accentColor + " opacity-60"}`} />
                        <AnimatePresence>
                          {!collapsed && (
                            <motion.div
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              exit={{ opacity: 0 }}
                              className="flex flex-col z-10 min-w-0"
                            >
                              <span className={`text-[11px] font-display font-semibold leading-none ${isActive ? "text-white" : "text-gray-400"}`}>{item.label}</span>
                              <span className="text-[8px] font-mono text-gray-700 mt-0.5">{item.desc}</span>
                            </motion.div>
                          )}
                        </AnimatePresence>
                        {/* Badge for incident count */}
                        {item.path === "/incidents" && incidentCount > 0 && !collapsed && (
                          <motion.span
                            initial={{ scale: 0 }} animate={{ scale: 1 }}
                            className="ml-auto z-10 text-[8px] font-mono px-1.5 py-0.5 rounded-full bg-red-500/20 border border-red-500/40 text-red-400"
                          >
                            {incidentCount}
                          </motion.span>
                        )}
                      </motion.div>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Bottom status */}
        <div className="shrink-0 p-2 border-t border-white/5 space-y-2">
          {!collapsed && (
            <div className="px-3 py-2 rounded-lg bg-black/30 flex items-center justify-between">
              <span className="text-[8px] font-mono text-gray-700 uppercase tracking-[0.2em]">SYS TIME</span>
              <span className="text-[10px] font-mono text-gray-400 tabular-nums">{time.toLocaleTimeString()}</span>
            </div>
          )}
          <div className={`flex items-center gap-2 px-3 py-2 rounded-lg bg-black/30 ${collapsed ? "justify-center" : ""}`}>
            <div className="shrink-0">
              <div className={connected ? "status-dot-live" : "status-dot-alert"} />
            </div>
            <AnimatePresence>
              {!collapsed && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col min-w-0">
                  <span className="text-[8px] font-mono text-gray-600 uppercase tracking-[0.2em]">Data Stream</span>
                  <span className={`text-[10px] font-display font-semibold ${connected ? "text-sentinel-success" : "text-sentinel-danger"}`}>
                    {connected ? "SECURE LINE" : "OFFLINE"}
                  </span>
                </motion.div>
              )}
            </AnimatePresence>
            {activityFlash && connected && !collapsed && (
              <motion.div initial={{ opacity: 0, scale: 0.5 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }} className="ml-auto">
                <Zap className="w-3 h-3 text-sentinel-accent" />
              </motion.div>
            )}
          </div>
        </div>

        {/* Collapse toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="absolute -right-3 top-24 w-6 h-6 rounded-full bg-sentinel-800 border border-sentinel-700/60 flex items-center justify-center text-gray-500 hover:text-white hover:bg-sentinel-700 transition-all z-30 shadow-lg"
        >
          {collapsed ? <ChevronRight className="w-3 h-3" /> : <ChevronLeft className="w-3 h-3" />}
        </button>
      </motion.aside>

      {/* ── Main ─────────────────────────────────────────────── */}
      <main className="flex-1 overflow-auto flex flex-col relative z-10">
        {/* Top bar */}
        <div
          className="shrink-0 flex items-center justify-between px-8 py-3 border-b border-white/5"
          style={{ background: "rgba(4,8,15,0.85)", backdropFilter: "blur(20px)" }}
        >
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-[10px] font-mono">
            <span className="text-gray-700 uppercase tracking-widest">NeuralOps</span>
            <span className="text-gray-800">/</span>
            <span className={`uppercase tracking-widest ${currentNav ? ACCENT_COLORS[currentNav.accent] : "text-sentinel-accent"}`}>
              {currentNav?.label ?? "Page"}
            </span>
          </div>
          {/* Status strip */}
          <div className="flex items-center gap-5">
            <div className="flex items-center gap-1.5 text-[9px] font-mono text-gray-600 uppercase tracking-widest">
              <Radio className="w-3 h-3 text-sentinel-accent animate-pulse" />
              <span>Autonomous Mode</span>
            </div>
            <div className="flex items-center gap-1.5 text-[9px] font-mono text-gray-600 uppercase tracking-widest">
              <ShieldCheck className="w-3 h-3 text-sentinel-success" />
              <span>Zero-Trust Enclave</span>
            </div>
            <div className={`flex items-center gap-1 text-[9px] font-mono uppercase tracking-widest ${connected ? "text-sentinel-success" : "text-sentinel-danger"}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${connected ? "bg-sentinel-success animate-pulse" : "bg-sentinel-danger"}`} />
              {connected ? "LIVE" : "OFFLINE"}
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={{ duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
