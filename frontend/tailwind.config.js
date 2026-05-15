/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        sentinel: {
          950: "#0a0e17",
          900: "#0f1629",
          800: "#1a2332",
          700: "#243044",
          500: "#3b82f6",
          400: "#60a5fa",
          accent: "#22d3ee",
          danger: "#ef4444",
          warning: "#f59e0b",
          success: "#10b981",
        },
      },
      fontFamily: {
        sans: ["JetBrains Mono", "ui-monospace", "monospace"],
        display: ["Space Grotesk", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
