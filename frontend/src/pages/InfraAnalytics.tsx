import React, { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "../lib/api";
import {
  BarChart3, TrendingUp, TrendingDown, Activity, AlertCircle,
  Cpu, HardDrive, Wifi, Clock, RefreshCw, ChevronDown
} from "lucide-react";

// Utility — generate sine-wave-ish sparkline data
function genSeries(base: number, len = 30, noise = 12): number[] {
  const pts: number[] = [];
  let val = base;
  for (let i = 0; i < len; i++) {
    val = Math.max(5, Math.min(98, val + (Math.random() - 0.48) * noise));
    pts.push(val);
  }
  return pts;
}

function Sparkline({ data, color, height = 40 }: { data: number[]; color: string; height?: number }) {
  const max = Math.max(...data, 1);
  const pts = data.map((v, i) => [
    (i / (data.length - 1)) * 180,
    height - (v / max) * (height - 4) - 2,
  ]);
  const path = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ");
  const area = `${path} L${pts[pts.length-1][0]},${height} L0,${height} Z`;
  return (
    <svg viewBox={`0 0 180 ${height}`} className="w-full" style={{ height }}>
      <defs>
        <linearGradient id={`sg-${color.replace("#","")}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.35" />
          <stop offset="100%" stopColor={color} stopOpacity="0.02" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#sg-${color.replace("#","")})`} />
      <path d={path} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function MetricCard({ title, value, unit, delta, color, series, icon }: any) {
  const isUp = delta >= 0;
  return (
    <motion.div whileHover={{ y: -2 }} className="metric-card">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-black/40 border border-sentinel-700/50 flex items-center justify-center" style={{ color }}>
            {icon}
          </div>
          <div>
            <p className="text-[9px] font-mono text-gray-500 uppercase tracking-widest">{title}</p>
            <div className="flex items-baseline gap-1 mt-0.5">
              <span className="text-2xl font-display font-bold text-white tabular-nums">{value}</span>
              <span className="text-xs font-mono text-gray-500">{unit}</span>
            </div>
          </div>
        </div>
        <div className={`flex items-center gap-1 text-[10px] font-mono ${isUp ? "text-red-400" : "text-green-400"}`}>
          {isUp ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
          <span>{Math.abs(delta).toFixed(1)}%</span>
        </div>
      </div>
      <Sparkline data={series} color={color} />
    </motion.div>
  );
}

const PERIODS = ["1H", "6H", "24H", "7D", "30D"];
const HEATMAP_COLS = 24;
const HEATMAP_ROWS = 7;

export default function InfraAnalytics() {
  const [period, setPeriod] = useState("24H");
  const [metrics, setMetrics] = useState({
    cpu:    { val: 67, delta: 8.2,  series: genSeries(67) },
    mem:    { val: 74, delta: 3.1,  series: genSeries(74) },
    net:    { val: 892, delta: -12, series: genSeries(60) },
    errors: { val: 23, delta: 41,   series: genSeries(20, 30, 8) },
  });
  const [heatmap, setHeatmap] = useState<number[][]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Generate heatmap (rows=days, cols=hours)
    const data: number[][] = Array.from({ length: HEATMAP_ROWS }, () =>
      Array.from({ length: HEATMAP_COLS }, () => Math.random())
    );
    setHeatmap(data);

    // Periodically refresh metrics
    const t = setInterval(() => {
      setMetrics(prev => ({
        cpu:    { val: Math.max(10, Math.min(95, prev.cpu.val   + (Math.random()-0.48)*5)), delta: (Math.random()-0.4)*15, series: [...prev.cpu.series.slice(1),   Math.max(10,Math.min(95,prev.cpu.val+(Math.random()-0.5)*8))] },
        mem:    { val: Math.max(10, Math.min(95, prev.mem.val   + (Math.random()-0.4)*3)),  delta: (Math.random()-0.4)*10, series: [...prev.mem.series.slice(1),   Math.max(10,Math.min(95,prev.mem.val+(Math.random()-0.5)*4))] },
        net:    { val: Math.max(10, Math.min(1900,prev.net.val  + (Math.random()-0.5)*80)), delta: (Math.random()-0.4)*20, series: [...prev.net.series.slice(1),   Math.max(10,Math.min(95,prev.net.val/20+(Math.random()-0.5)*8))] },
        errors: { val: Math.max(0, Math.min(200, prev.errors.val+(Math.random()-0.4)*10)), delta: (Math.random()-0.3)*30,  series: [...prev.errors.series.slice(1),Math.max(0, Math.min(50, prev.errors.val+(Math.random()-0.4)*6))] },
      }));
    }, 3000);
    return () => clearInterval(t);
  }, []);

  const heatColor = (val: number): string => {
    if (val < 0.2) return "rgba(16,185,129,0.6)";
    if (val < 0.5) return "rgba(245,158,11,0.5)";
    if (val < 0.75) return "rgba(249,115,22,0.6)";
    return "rgba(239,68,68,0.75)";
  };

  return (
    <div className="h-full flex flex-col gap-6">
      {/* Header */}
      <header className="flex items-end justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-cyan-500/10 border border-cyan-500/30 rounded-xl flex items-center justify-center shadow-[0_0_25px_rgba(34,211,238,0.2)]">
            <BarChart3 className="w-6 h-6 text-cyan-400" />
          </div>
          <div>
            <h1 className="page-title glow-text-accent">Infrastructure Analytics</h1>
            <p className="text-[10px] font-mono text-gray-500 uppercase tracking-widest mt-1">Real-time observability · Predictive intelligence</p>
          </div>
        </div>
        {/* Period picker */}
        <div className="flex items-center gap-2">
          {PERIODS.map(p => (
            <button
              key={p}
              onClick={() => { setPeriod(p); setHeatmap(Array.from({ length: HEATMAP_ROWS }, () => Array.from({ length: HEATMAP_COLS }, () => Math.random()))); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono uppercase tracking-widest transition-all ${period === p ? "bg-sentinel-accent/20 border border-sentinel-accent/50 text-sentinel-accent" : "border border-sentinel-700/40 text-gray-500 hover:text-white hover:border-sentinel-700"}`}
            >
              {p}
            </button>
          ))}
        </div>
      </header>

      {/* Metric cards */}
      <div className="grid grid-cols-4 gap-4">
        <MetricCard title="CPU Avg" value={metrics.cpu.val.toFixed(0)} unit="%" delta={metrics.cpu.delta} color="#22d3ee" series={metrics.cpu.series} icon={<Cpu className="w-4 h-4" />} />
        <MetricCard title="Mem Usage" value={metrics.mem.val.toFixed(0)} unit="%" delta={metrics.mem.delta} color="#f59e0b" series={metrics.mem.series} icon={<HardDrive className="w-4 h-4" />} />
        <MetricCard title="Net I/O" value={metrics.net.val.toFixed(0)} unit="Mbps" delta={metrics.net.delta} color="#8b5cf6" series={metrics.net.series} icon={<Wifi className="w-4 h-4" />} />
        <MetricCard title="Error Rate" value={metrics.errors.val.toFixed(0)} unit="/min" delta={metrics.errors.delta} color="#ef4444" series={metrics.errors.series} icon={<AlertCircle className="w-4 h-4" />} />
      </div>

      {/* Anomaly heatmap */}
      <div className="glass-panel rounded-xl border border-sentinel-700/50 p-5 flex-1 flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-display font-semibold text-white">Anomaly Heatmap</h3>
            <p className="text-[9px] font-mono text-gray-500 uppercase tracking-widest mt-0.5">Error intensity by day × hour</p>
          </div>
          <div className="flex items-center gap-3 text-[9px] font-mono">
            {[["Low", "rgba(16,185,129,0.6)"], ["Medium", "rgba(245,158,11,0.5)"], ["High", "rgba(249,115,22,0.6)"], ["Critical", "rgba(239,68,68,0.75)"]].map(([l, c]) => (
              <div key={l} className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-sm" style={{ background: c as string }} />
                <span className="text-gray-500">{l}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="flex-1 overflow-hidden">
          {/* Hour axis */}
          <div className="flex pl-8 mb-1">
            {Array.from({ length: HEATMAP_COLS }, (_, i) => (
              <div key={i} className="flex-1 text-center text-[8px] font-mono text-gray-700">
                {i % 6 === 0 ? `${i}h` : ""}
              </div>
            ))}
          </div>
          {/* Cells */}
          {heatmap.map((row, ri) => (
            <div key={ri} className="flex items-center gap-0.5 mb-0.5">
              <span className="w-8 text-[8px] font-mono text-gray-600 shrink-0">
                {["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][ri]}
              </span>
              {row.map((val, ci) => (
                <motion.div
                  key={ci}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: (ri * HEATMAP_COLS + ci) * 0.001 }}
                  title={`${["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][ri]} ${ci}:00 — ${(val*100).toFixed(0)}% load`}
                  className="flex-1 rounded-sm cursor-pointer hover:ring-1 hover:ring-white/30 transition-all"
                  style={{ height: 22, background: heatColor(val) }}
                />
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
