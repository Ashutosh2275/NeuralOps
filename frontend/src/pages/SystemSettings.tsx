import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useSettings, PlatformSettings } from "../contexts/SettingsContext";
import {
  Palette, Zap, Wifi, Brain, Film, RotateCcw, Save,
  Check, ChevronRight, Monitor, Sliders, Cpu
} from "lucide-react";

// ── Section definitions ─────────────────────────────────────────────────────
type SectionId = "theme" | "performance" | "websocket" | "ai" | "replay";

const SECTIONS: { id: SectionId; label: string; icon: React.ReactNode; color: string }[] = [
  { id: "theme",       label: "Theme & Visuals",   icon: <Palette className="w-4 h-4" />,  color: "text-sentinel-accent" },
  { id: "performance", label: "Performance",        icon: <Zap className="w-4 h-4" />,      color: "text-yellow-400"      },
  { id: "websocket",   label: "WebSocket",          icon: <Wifi className="w-4 h-4" />,     color: "text-blue-400"        },
  { id: "ai",          label: "AI Settings",        icon: <Brain className="w-4 h-4" />,    color: "text-purple-400"      },
  { id: "replay",      label: "Replay & Demo",      icon: <Film className="w-4 h-4" />,     color: "text-orange-400"      },
];

// ── Reusable controls ──────────────────────────────────────────────────────
function Toggle({ value, onChange, label, sub }: { value: boolean; onChange: (v: boolean) => void; label: string; sub?: string }) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-sentinel-700/20 last:border-0">
      <div>
        <p className="text-sm font-display text-white font-medium">{label}</p>
        {sub && <p className="text-[10px] font-mono text-gray-600 mt-0.5">{sub}</p>}
      </div>
      <button
        onClick={() => onChange(!value)}
        className={`relative w-11 h-6 rounded-full transition-all duration-300 shrink-0 ${value ? "bg-sentinel-accent/80" : "bg-sentinel-800"}`}
        style={{ boxShadow: value ? "0 0 12px rgba(34,211,238,0.4)" : "none" }}
      >
        <motion.div animate={{ x: value ? 22 : 2 }} transition={{ type: "spring", stiffness: 500, damping: 30 }}
          className="absolute top-1 w-4 h-4 rounded-full bg-white shadow-md" />
      </button>
    </div>
  );
}

function RangeSlider({ value, onChange, label, sub, min, max, unit }: {
  value: number; onChange: (v: number) => void; label: string; sub?: string; min: number; max: number; unit?: string;
}) {
  return (
    <div className="py-3 border-b border-sentinel-700/20 last:border-0">
      <div className="flex items-center justify-between mb-2">
        <div>
          <p className="text-sm font-display text-white font-medium">{label}</p>
          {sub && <p className="text-[10px] font-mono text-gray-600 mt-0.5">{sub}</p>}
        </div>
        <span className="text-sm font-display font-bold text-sentinel-accent tabular-nums">{value}{unit ?? "%"}</span>
      </div>
      <input type="range" min={min} max={max} value={value} onChange={e => onChange(Number(e.target.value))}
        className="w-full accent-cyan-400" />
    </div>
  );
}

// ── Section content ────────────────────────────────────────────────────────
function ThemeSection({ settings, set }: { settings: PlatformSettings; set: <K extends keyof PlatformSettings>(k: K, v: PlatformSettings[K]) => void }) {
  return (
    <div className="space-y-0">
      <Toggle value={settings.scanlines}   onChange={v => set("scanlines", v)}   label="Scanlines"     sub="CRT scanline overlay for cinematic effect" />
      <Toggle value={settings.cyberGrid}   onChange={v => set("cyberGrid", v)}   label="Cyber Grid"    sub="Background dot-grid pattern" />
      <Toggle value={settings.glowEffects} onChange={v => set("glowEffects", v)} label="Glow Effects"  sub="Neon glow on nodes, cards, and buttons" />
      <Toggle value={settings.particleFlow}onChange={v => set("particleFlow", v)}label="Particle Flow" sub="Animated packet particles on topology edges" />
      <Toggle value={settings.animations}  onChange={v => set("animations", v)}  label="Animations"    sub="Framer Motion transitions and micro-interactions" />
      <RangeSlider value={settings.glowIntensity} onChange={v => set("glowIntensity", v)} label="Glow Intensity" sub="Controls neon glow brightness globally" min={0} max={100} />
      <RangeSlider value={settings.animSpeed}     onChange={v => set("animSpeed", v)}     label="Animation Speed" sub="Higher = faster transitions"             min={20} max={150} />
    </div>
  );
}

function PerformanceSection({ settings, set }: { settings: PlatformSettings; set: <K extends keyof PlatformSettings>(k: K, v: PlatformSettings[K]) => void }) {
  return (
    <div>
      <RangeSlider value={settings.d3Quality} onChange={v => set("d3Quality", v)} label="D3 Render Quality" sub="Higher quality = more CPU usage in topology" min={20} max={100} />
      <div className="mt-4 p-3 rounded-lg bg-yellow-500/5 border border-yellow-500/20">
        <p className="text-[10px] font-mono text-yellow-400 uppercase tracking-widest mb-1">Performance Mode</p>
        <p className="text-[10px] font-mono text-gray-500">Set D3 quality ≤ 50 for smoother rendering on lower-end hardware. Topology node count remains unchanged.</p>
      </div>
    </div>
  );
}

function WebSocketSection({ settings, set }: { settings: PlatformSettings; set: <K extends keyof PlatformSettings>(k: K, v: PlatformSettings[K]) => void }) {
  return (
    <div>
      <Toggle value={settings.wsReconnect} onChange={v => set("wsReconnect", v)} label="Auto Reconnect" sub="Automatically reconnect on connection loss" />
      <Toggle value={settings.wsDebug}     onChange={v => set("wsDebug", v)}     label="Debug Mode"     sub="Log all WebSocket messages to console" />
      <RangeSlider value={settings.wsRateLimit} onChange={v => set("wsRateLimit", v)} label="Rate Limit" sub="Max messages per second processed from stream" min={10} max={500} unit="/s" />
    </div>
  );
}

function AISection({ settings, set }: { settings: PlatformSettings; set: <K extends keyof PlatformSettings>(k: K, v: PlatformSettings[K]) => void }) {
  return (
    <div>
      <Toggle value={settings.autoRemediation} onChange={v => set("autoRemediation", v)} label="Autonomous Remediation" sub="Allow AI to execute kubectl commands automatically" />
      <RangeSlider value={settings.aiConfThreshold} onChange={v => set("aiConfThreshold", v)} label="Confidence Threshold" sub="Minimum AI confidence required to trigger remediation" min={50} max={99} />
      <RangeSlider value={settings.maxReasoning}    onChange={v => set("maxReasoning", v)}    label="Max Reasoning Log"   sub="Maximum entries retained in the cognitive stream"     min={10} max={200} unit=" entries" />
    </div>
  );
}

function ReplaySection({ settings, set }: { settings: PlatformSettings; set: <K extends keyof PlatformSettings>(k: K, v: PlatformSettings[K]) => void }) {
  return (
    <div>
      <Toggle value={settings.replayAutoplay}   onChange={v => set("replayAutoplay", v)}   label="Auto-play Replay"     sub="Begin replay automatically when opened" />
      <Toggle value={settings.replayCinematic}  onChange={v => set("replayCinematic", v)}  label="Cinematic Mode"       sub="Dramatic camera movements and transitions during replay" />
      <RangeSlider value={settings.replaySpeed} onChange={v => set("replaySpeed", v)}      label="Replay Speed" sub="Default playback speed (100 = 1×, 200 = 2×)" min={25} max={400} unit="%" />
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────
export default function SystemSettings() {
  const { settings, set, reset } = useSettings();
  const [active, setActive] = useState<SectionId>("theme");
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const renderSection = () => {
    switch (active) {
      case "theme":       return <ThemeSection settings={settings} set={set} />;
      case "performance": return <PerformanceSection settings={settings} set={set} />;
      case "websocket":   return <WebSocketSection settings={settings} set={set} />;
      case "ai":          return <AISection settings={settings} set={set} />;
      case "replay":      return <ReplaySection settings={settings} set={set} />;
    }
  };

  const activeSection = SECTIONS.find(s => s.id === active)!;

  return (
    <div className="h-full flex flex-col gap-6">
      {/* Header */}
      <header className="flex items-end justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-gray-500/10 border border-gray-500/30 rounded-xl flex items-center justify-center">
            <Sliders className="w-6 h-6 text-gray-400" />
          </div>
          <div>
            <h1 className="page-title">System Settings</h1>
            <p className="text-[10px] font-mono text-gray-500 uppercase tracking-widest mt-1">
              Platform configuration · UI customization · Demo controls
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={reset}
            className="flex items-center gap-2 px-4 py-2 rounded-xl glass-panel border border-sentinel-700/50 text-gray-400 hover:text-white hover:border-sentinel-accent/30 text-xs font-mono uppercase tracking-widest transition-all">
            <RotateCcw className="w-3.5 h-3.5" /> Reset Defaults
          </button>
          <motion.button onClick={handleSave} whileTap={{ scale: 0.96 }}
            className="flex items-center gap-2 px-5 py-2 rounded-xl bg-sentinel-accent/20 border border-sentinel-accent/40 text-sentinel-accent text-xs font-mono uppercase tracking-widest hover:bg-sentinel-accent/30 transition-all"
            style={{ boxShadow: "0 0 16px rgba(34,211,238,0.15)" }}>
            {saved ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Save className="w-3.5 h-3.5" />}
            {saved ? "Saved!" : "Save Settings"}
          </motion.button>
        </div>
      </header>

      <div className="grid grid-cols-12 gap-6 flex-1 min-h-0">
        {/* Sidebar nav */}
        <div className="col-span-3 space-y-1">
          {SECTIONS.map(section => (
            <button key={section.id} onClick={() => setActive(section.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all duration-200 ${active === section.id
                ? "glass-panel border border-sentinel-accent/25 bg-sentinel-accent/5"
                : "hover:bg-white/3 border border-transparent"
              }`}>
              <span className={active === section.id ? "text-sentinel-accent" : section.color + " opacity-50"}>
                {section.icon}
              </span>
              <span className={`text-xs font-display font-semibold ${active === section.id ? "text-white" : "text-gray-500"}`}>
                {section.label}
              </span>
              {active === section.id && <ChevronRight className="w-3 h-3 text-sentinel-accent ml-auto" />}
            </button>
          ))}

          {/* Live status indicators */}
          <div className="mt-6 p-4 rounded-xl glass-panel border border-sentinel-700/30">
            <p className="text-[9px] font-mono text-gray-600 uppercase tracking-widest mb-3">Live Overrides</p>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-[9px] font-mono">
                <span className="text-gray-600">Scanlines</span>
                <span className={settings.scanlines ? "text-green-400" : "text-gray-600"}>
                  {settings.scanlines ? "ON" : "OFF"}
                </span>
              </div>
              <div className="flex items-center justify-between text-[9px] font-mono">
                <span className="text-gray-600">Glow</span>
                <span className={settings.glowEffects ? "text-cyan-400" : "text-gray-600"}>
                  {settings.glowEffects ? `${settings.glowIntensity}%` : "OFF"}
                </span>
              </div>
              <div className="flex items-center justify-between text-[9px] font-mono">
                <span className="text-gray-600">Auto-remediation</span>
                <span className={settings.autoRemediation ? "text-green-400" : "text-red-400"}>
                  {settings.autoRemediation ? "ENABLED" : "DISABLED"}
                </span>
              </div>
              <div className="flex items-center justify-between text-[9px] font-mono">
                <span className="text-gray-600">AI Confidence</span>
                <span className="text-purple-400">{settings.aiConfThreshold}%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Settings content */}
        <div className="col-span-9">
          <AnimatePresence mode="wait">
            <motion.div key={active} initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }} transition={{ duration: 0.2 }}
              className="glass-panel rounded-xl border border-sentinel-700/40 overflow-hidden h-full">
              {/* Section header */}
              <div className="px-6 py-4 border-b border-sentinel-700/40 flex items-center gap-3">
                <span className={activeSection.color}>{activeSection.icon}</span>
                <h2 className="text-sm font-display font-bold text-white">{activeSection.label}</h2>
                <span className="text-[9px] font-mono text-gray-600 ml-2 uppercase tracking-widest">
                  Changes apply instantly · Persisted to localStorage
                </span>
              </div>
              <div className="px-6 py-2 overflow-y-auto h-full">
                {renderSection()}
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
