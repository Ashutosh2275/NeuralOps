/**
 * SettingsContext — Persistent platform configuration.
 * All settings are persisted to localStorage and applied live via CSS custom properties.
 */
import React, { createContext, useContext, useEffect, useState } from "react";

export interface PlatformSettings {
  // Visuals
  scanlines: boolean;
  cyberGrid: boolean;
  glowEffects: boolean;
  particleFlow: boolean;
  animations: boolean;
  glowIntensity: number;   // 0-100
  animSpeed: number;        // 20-150
  // Performance
  d3Quality: number;        // 20-100
  // WebSocket
  wsReconnect: boolean;
  wsDebug: boolean;
  wsRateLimit: number;
  // AI
  autoRemediation: boolean;
  aiConfThreshold: number;
  maxReasoning: number;
  // Replay
  replayAutoplay: boolean;
  replayCinematic: boolean;
  replaySpeed: number;
}

const DEFAULTS: PlatformSettings = {
  scanlines: true, cyberGrid: true, glowEffects: true,
  particleFlow: true, animations: true, glowIntensity: 75, animSpeed: 80,
  d3Quality: 90, wsReconnect: true, wsDebug: false, wsRateLimit: 100,
  autoRemediation: true, aiConfThreshold: 75, maxReasoning: 60,
  replayAutoplay: false, replayCinematic: true, replaySpeed: 100,
};

const KEY = "netraai-settings-v2";

interface SettingsContextType {
  settings: PlatformSettings;
  set: <K extends keyof PlatformSettings>(key: K, value: PlatformSettings[K]) => void;
  reset: () => void;
}

const SettingsContext = createContext<SettingsContextType | null>(null);

export const SettingsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [settings, setSettings] = useState<PlatformSettings>(() => {
    try {
      const saved = localStorage.getItem(KEY);
      return saved ? { ...DEFAULTS, ...JSON.parse(saved) } : DEFAULTS;
    } catch { return DEFAULTS; }
  });

  // Apply settings to DOM as CSS custom properties + class toggles
  useEffect(() => {
    const root = document.documentElement;
    // Scanlines
    root.style.setProperty("--scanlines-opacity", settings.scanlines ? "0.25" : "0");
    // Cyber grid
    root.style.setProperty("--grid-opacity", settings.cyberGrid ? "1" : "0");
    // Glow
    const glowBase = settings.glowEffects ? (settings.glowIntensity / 100) : 0;
    root.style.setProperty("--glow-accent-opacity", String(glowBase * 0.55));
    root.style.setProperty("--glow-danger-opacity", String(glowBase * 0.55));
    // Animation speed
    root.style.setProperty("--animation-speed", `${100 / settings.animSpeed}s`);
    // Toggle animation class
    if (!settings.animations) {
      root.classList.add("reduce-motion");
    } else {
      root.classList.remove("reduce-motion");
    }
    // Persist
    localStorage.setItem(KEY, JSON.stringify(settings));
  }, [settings]);

  const set = <K extends keyof PlatformSettings>(key: K, value: PlatformSettings[K]) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const reset = () => setSettings(DEFAULTS);

  return (
    <SettingsContext.Provider value={{ settings, set, reset }}>
      {children}
    </SettingsContext.Provider>
  );
};

export function useSettings() {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error("useSettings must be used within SettingsProvider");
  return ctx;
}
