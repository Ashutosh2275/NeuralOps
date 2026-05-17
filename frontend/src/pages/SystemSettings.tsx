import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Settings, Palette, Wifi, Cpu, Film, Zap, Moon, Sun, Check, ChevronDown } from "lucide-react";

interface ToggleProps { value: boolean; onChange: (v: boolean) => void; color?: string; }
function Toggle({ value, onChange, color = "bg-sentinel-accent" }: ToggleProps) {
  return (
    <button
      onClick={() => onChange(!value)}
      className={`relative w-10 h-5 rounded-full transition-all duration-200 ${value ? color : "bg-sentinel-700"}`}
    >
      <motion.div
        animate={{ x: value ? 20 : 2 }}
        transition={{ type: "spring", stiffness: 500, damping: 30 }}
        className="absolute top-0.5 w-4 h-4 rounded-full bg-white shadow"
      />
    </button>
  );
}

interface SliderProps { value: number; min: number; max: number; onChange: (v: number) => void; }
function Slider({ value, min, max, onChange }: SliderProps) {
  return (
    <input
      type="range" min={min} max={max} value={value}
      onChange={e => onChange(Number(e.target.value))}
      className="w-full h-1 rounded-full accent-sentinel-accent cursor-pointer"
    />
  );
}

const SECTIONS = [
  { id: "theme",       label: "Theme & Visuals",     icon: <Palette className="w-4 h-4" /> },
  { id: "performance", label: "Performance",          icon: <Zap className="w-4 h-4" /> },
  { id: "ws",          label: "WebSocket",            icon: <Wifi className="w-4 h-4" /> },
  { id: "ai",          label: "AI Settings",          icon: <Cpu className="w-4 h-4" /> },
  { id: "replay",      label: "Replay & Demo",        icon: <Film className="w-4 h-4" /> },
];

export default function SystemSettings() {
  const [activeSection, setActiveSection] = useState("theme");
  const [settings, setSettings] = useState({
    darkMode:         true,
    scanlines:        true,
    cyberGrid:        true,
    particleFlow:     true,
    glowEffects:      true,
    animations:       true,
    animSpeed:        80,
    d3Quality:        90,
    wsReconnect:      true,
    wsDebug:          false,
    wsRateLimit:      100,
    autoRemediation:  true,
    aiConfThreshold:  75,
    maxReasoning:     60,
    replayAutoplay:   false,
    replayCinematic:  true,
    replaySpeed:      100,
  });

  const set = <K extends keyof typeof settings>(k: K, v: typeof settings[K]) =>
    setSettings(s => ({ ...s, [k]: v }));

  const [saved, setSaved] = useState(false);
  const save = () => { setSaved(true); setTimeout(() => setSaved(false), 2000); };

  return (
    <div className="h-full flex flex-col gap-6">
      <header className="flex items-end justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-gray-500/10 border border-gray-500/30 rounded-xl flex items-center justify-center">
            <Settings className="w-6 h-6 text-gray-400" />
          </div>
          <div>
            <h1 className="page-title">System Settings</h1>
            <p className="text-[10px] font-mono text-gray-500 uppercase tracking-widest mt-1">Platform configuration · UI customization · Demo controls</p>
          </div>
        </div>
        <motion.button
          whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
          onClick={save}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl border font-display font-semibold text-sm transition-all ${saved ? "bg-green-500/20 border-green-500/50 text-green-400" : "bg-sentinel-accent/15 border-sentinel-accent/40 text-sentinel-accent"}`}
        >
          {saved ? <><Check className="w-4 h-4" /> Saved!</> : "Save Settings"}
        </motion.button>
      </header>

      <div className="flex gap-6 flex-1 min-h-0">
        {/* Sidebar nav */}
        <div className="w-52 shrink-0 space-y-1">
          {SECTIONS.map(s => (
            <button
              key={s.id}
              onClick={() => setActiveSection(s.id)}
              className={`nav-item w-full text-left ${activeSection === s.id ? "active" : "text-gray-400"}`}
            >
              {s.icon}
              <span>{s.label}</span>
            </button>
          ))}
        </div>

        {/* Settings panels */}
        <div className="flex-1 overflow-y-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeSection}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.2 }}
              className="glass-panel rounded-xl border border-sentinel-700/50 p-6 space-y-6"
            >
              {activeSection === "theme" && (
                <>
                  <h2 className="text-base font-display font-bold text-white border-b border-sentinel-700/40 pb-3">Theme & Visuals</h2>
                  <div className="space-y-5">
                    {[
                      ["Dark Mode",       "darkMode",      "Always-on dark cinematic theme"],
                      ["Scanlines",       "scanlines",     "CRT scanline overlay for cinematic effect"],
                      ["Cyber Grid",      "cyberGrid",     "Background dot-grid pattern"],
                      ["Particle Flow",   "particleFlow",  "Animated packet particles on topology edges"],
                      ["Glow Effects",    "glowEffects",   "Neon glow on nodes, cards, and buttons"],
                      ["Animations",      "animations",    "Framer Motion transitions and micro-interactions"],
                    ].map(([label, key, desc]) => (
                      <div key={key} className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-sans text-white">{label}</p>
                          <p className="text-[10px] font-mono text-gray-500 mt-0.5">{desc}</p>
                        </div>
                        <Toggle value={settings[key as keyof typeof settings] as boolean} onChange={v => set(key as keyof typeof settings, v as any)} />
                      </div>
                    ))}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm font-sans text-white">Animation Speed</p>
                        <span className="text-xs font-mono text-sentinel-accent">{settings.animSpeed}%</span>
                      </div>
                      <Slider value={settings.animSpeed} min={20} max={150} onChange={v => set("animSpeed", v)} />
                    </div>
                  </div>
                </>
              )}
              {activeSection === "performance" && (
                <>
                  <h2 className="text-base font-display font-bold text-white border-b border-sentinel-700/40 pb-3">Performance Settings</h2>
                  <div className="space-y-5">
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <p className="text-sm font-sans text-white">D3 Render Quality</p>
                          <p className="text-[10px] font-mono text-gray-500">Higher = more particles, better glow (may reduce FPS)</p>
                        </div>
                        <span className="text-xs font-mono text-sentinel-accent">{settings.d3Quality}%</span>
                      </div>
                      <Slider value={settings.d3Quality} min={20} max={100} onChange={v => set("d3Quality", v)} />
                    </div>
                    {[
                      ["Animations", "animations", "Enable framer-motion transitions"],
                      ["Glow Effects", "glowEffects", "SVG filter glow (GPU-accelerated)"],
                    ].map(([label, key, desc]) => (
                      <div key={key} className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-sans text-white">{label}</p>
                          <p className="text-[10px] font-mono text-gray-500">{desc}</p>
                        </div>
                        <Toggle value={settings[key as keyof typeof settings] as boolean} onChange={v => set(key as keyof typeof settings, v as any)} />
                      </div>
                    ))}
                  </div>
                </>
              )}
              {activeSection === "ws" && (
                <>
                  <h2 className="text-base font-display font-bold text-white border-b border-sentinel-700/40 pb-3">WebSocket Settings</h2>
                  <div className="space-y-5">
                    {[
                      ["Auto Reconnect", "wsReconnect", "Automatically reconnect on disconnect"],
                      ["Debug Mode",     "wsDebug",     "Log all WS messages to console"],
                    ].map(([label, key, desc]) => (
                      <div key={key} className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-sans text-white">{label}</p>
                          <p className="text-[10px] font-mono text-gray-500">{desc}</p>
                        </div>
                        <Toggle value={settings[key as keyof typeof settings] as boolean} onChange={v => set(key as keyof typeof settings, v as any)} />
                      </div>
                    ))}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <p className="text-sm font-sans text-white">Event Buffer Rate Limit</p>
                          <p className="text-[10px] font-mono text-gray-500">Max events/second to render</p>
                        </div>
                        <span className="text-xs font-mono text-sentinel-accent">{settings.wsRateLimit}/s</span>
                      </div>
                      <Slider value={settings.wsRateLimit} min={10} max={500} onChange={v => set("wsRateLimit", v)} />
                    </div>
                  </div>
                </>
              )}
              {activeSection === "ai" && (
                <>
                  <h2 className="text-base font-display font-bold text-white border-b border-sentinel-700/40 pb-3">AI Settings</h2>
                  <div className="space-y-5">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-sans text-white">Autonomous Remediation</p>
                        <p className="text-[10px] font-mono text-gray-500">Allow AI to apply kubectl fixes automatically</p>
                      </div>
                      <Toggle value={settings.autoRemediation} onChange={v => set("autoRemediation", v)} color="bg-green-500" />
                    </div>
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <p className="text-sm font-sans text-white">Confidence Threshold</p>
                          <p className="text-[10px] font-mono text-gray-500">Min confidence before autonomous action</p>
                        </div>
                        <span className="text-xs font-mono text-sentinel-accent">{settings.aiConfThreshold}%</span>
                      </div>
                      <Slider value={settings.aiConfThreshold} min={50} max={99} onChange={v => set("aiConfThreshold", v)} />
                    </div>
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <p className="text-sm font-sans text-white">Reasoning Log Buffer</p>
                          <p className="text-[10px] font-mono text-gray-500">Max messages to keep in streaming log</p>
                        </div>
                        <span className="text-xs font-mono text-sentinel-accent">{settings.maxReasoning}</span>
                      </div>
                      <Slider value={settings.maxReasoning} min={10} max={200} onChange={v => set("maxReasoning", v)} />
                    </div>
                  </div>
                </>
              )}
              {activeSection === "replay" && (
                <>
                  <h2 className="text-base font-display font-bold text-white border-b border-sentinel-700/40 pb-3">Replay & Demo Settings</h2>
                  <div className="space-y-5">
                    {[
                      ["Auto-Play Replay",   "replayAutoplay",  "Start replay automatically on page open"],
                      ["Cinematic Mode",     "replayCinematic", "Enable camera transitions and overlays"],
                    ].map(([label, key, desc]) => (
                      <div key={key} className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-sans text-white">{label}</p>
                          <p className="text-[10px] font-mono text-gray-500">{desc}</p>
                        </div>
                        <Toggle value={settings[key as keyof typeof settings] as boolean} onChange={v => set(key as keyof typeof settings, v as any)} />
                      </div>
                    ))}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <p className="text-sm font-sans text-white">Default Replay Speed</p>
                          <p className="text-[10px] font-mono text-gray-500">Playback rate (100% = realtime)</p>
                        </div>
                        <span className="text-xs font-mono text-sentinel-accent">{settings.replaySpeed}%</span>
                      </div>
                      <Slider value={settings.replaySpeed} min={25} max={400} onChange={v => set("replaySpeed", v)} />
                    </div>
                  </div>
                </>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
