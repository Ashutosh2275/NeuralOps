/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        sentinel: {
          950: "#07090f",
          900: "#0b1322",
          800: "#0f1a2e",
          700: "#142238",
          600: "#1a2d47",
          accent:   "#22d3ee",
          danger:   "#ef4444",
          warning:  "#f59e0b",
          success:  "#10b981",
          purple:   "#a855f7",
        },
      },
      fontFamily: {
        sans:    ["JetBrains Mono", "ui-monospace", "monospace"],
        display: ["Space Grotesk", "system-ui", "sans-serif"],
        mono:    ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "spin-slow":  "spin 8s linear infinite",
        "float":      "float 4s ease-in-out infinite",
        "ai-glow":    "ai-glow-pulse 2.2s ease-in-out infinite",
        "shimmer":    "shimmer 1.8s ease-in-out infinite",
        "count-up":   "count-up 0.4s ease-out forwards",
      },
      boxShadow: {
        "neon-cyan":  "0 0 20px rgba(34,211,238,0.3)",
        "neon-red":   "0 0 20px rgba(239,68,68,0.3)",
        "neon-green": "0 0 18px rgba(16,185,129,0.3)",
        "glass":      "0 4px 24px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.04)",
      },
    },
  },
  plugins: [],
};
