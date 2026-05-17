/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        sentinel: {
          950: "#04080f",
          900: "hsl(var(--sentinel-900))",
          800: "hsl(var(--sentinel-800))",
          700: "hsl(var(--sentinel-700))",
          600: "hsl(var(--sentinel-600))",
          accent:   "hsl(var(--sentinel-accent))",
          danger:   "hsl(var(--sentinel-danger))",
          warning:  "hsl(var(--sentinel-warning))",
          success:  "hsl(var(--sentinel-success))",
          purple:   "hsl(var(--sentinel-purple))",
        },
      },
      fontFamily: {
        sans:    ["JetBrains Mono", "ui-monospace", "monospace"],
        display: ["Space Grotesk", "system-ui", "sans-serif"],
        mono:    ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      animation: {
        "pulse-slow":  "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "spin-slow":   "spin 8s linear infinite",
        "float":       "float 4s ease-in-out infinite",
        "ai-glow":     "ai-glow-pulse 2s ease-in-out infinite",
        "shimmer":     "shimmer 1.6s ease-in-out infinite",
        "count-up":    "count-up 0.5s ease-out forwards",
      },
      backdropBlur: { xs: "2px" },
      boxShadow: {
        "neon-cyan":  "0 0 20px rgba(34,211,238,0.4)",
        "neon-red":   "0 0 20px rgba(239,68,68,0.4)",
        "neon-green": "0 0 20px rgba(52,211,153,0.35)",
        "glass":      "0 4px 30px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04)",
      },
    },
  },
  plugins: [],
};
