import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, Zap, TrendingUp, Shield, ChevronRight } from "lucide-react";
import type { WSEvent } from "../../hooks/useWebSocket";

interface AIInsight {
  agent: string;
  findings: string[];
  confidence: number;
  reasoning: string;
}

interface Props {
  insights: AIInsight[];
  wsEvents: WSEvent[];
}

const AGENT_META: Record<string, { color: string; icon: React.ReactElement; label: string }> = {
  cpu:            { color: "text-red-400",    icon: <Zap className="w-3 h-3" />,        label: "CPU Monitor"     },
  memory:         { color: "text-orange-400", icon: <Zap className="w-3 h-3" />,        label: "Mem Monitor"     },
  network:        { color: "text-blue-400",   icon: <Zap className="w-3 h-3" />,        label: "Net Monitor"     },
  logs:           { color: "text-cyan-400",   icon: <Zap className="w-3 h-3" />,        label: "Log Analyzer"    },
  rca:            { color: "text-green-400",  icon: <Brain className="w-3 h-3" />,      label: "RCA Engine"      },
  correlation:    { color: "text-yellow-400", icon: <TrendingUp className="w-3 h-3" />, label: "Correlator"      },
  recommendation: { color: "text-indigo-400", icon: <Shield className="w-3 h-3" />,     label: "Recommender"     },
};

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.min(1, Math.max(0, value)) * 100;
  const color = pct >= 80 ? "#10b981" : pct >= 60 ? "#f59e0b" : "#ef4444";
  return (
    <div className="w-full h-1 bg-sentinel-800 rounded-full overflow-hidden">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.7, ease: "easeOut" }}
        className="h-full rounded-full"
        style={{ background: color, boxShadow: `0 0 6px ${color}` }}
      />
    </div>
  );
}

export default function AIInsightsPanel({ insights, wsEvents }: Props) {
  const aiEvents = wsEvents.filter(e => e.type === "ai_insight").slice(0, 8);
  const allInsights: AIInsight[] = [
    ...insights,
    ...aiEvents.map((e: any) => ({
      agent:      e.payload?.agent     ?? "unknown",
      findings:   e.payload?.findings  ?? [],
      confidence: e.payload?.confidence ?? 0,
      reasoning:  e.payload?.reasoning  ?? "",
    })),
  ].slice(0, 6);

  return (
    <div className="glass-panel rounded-xl border border-sentinel-700/50 overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-sentinel-700/40 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-sentinel-accent/10 border border-sentinel-accent/30 flex items-center justify-center">
            <Brain className="w-4 h-4 text-sentinel-accent" />
          </div>
          <div>
            <h3 className="text-sm font-display font-semibold text-white">AI Analysis</h3>
            <p className="text-[9px] font-mono text-gray-500 uppercase tracking-widest mt-0.5">
              Multi-agent insights
            </p>
          </div>
        </div>
        <span className="text-[9px] font-mono text-sentinel-accent/60 uppercase tracking-widest">
          {allInsights.length} signals
        </span>
      </div>

      {/* Insights */}
      <div className="p-4 space-y-3">
        <AnimatePresence mode="popLayout">
          {allInsights.map((insight, idx) => {
            const meta = AGENT_META[insight.agent] ?? { color: "text-gray-400", icon: <Zap className="w-3 h-3" />, label: insight.agent };
            const pct  = Math.round(insight.confidence * 100);

            return (
              <motion.div
                key={`${insight.agent}-${idx}`}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                transition={{ delay: idx * 0.05 }}
                className="glass-panel-light rounded-lg p-3 space-y-2 hover:border-sentinel-accent/20 transition-all group"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={meta.color}>{meta.icon}</span>
                    <span className={`text-[10px] font-mono font-semibold uppercase tracking-widest ${meta.color}`}>
                      {meta.label}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-gray-500 tabular-nums">{pct}%</span>
                </div>

                <ConfidenceBar value={insight.confidence} />

                {insight.findings[0] && (
                  <p className="text-xs font-sans text-gray-300 leading-relaxed line-clamp-2">
                    {insight.findings[0]}
                  </p>
                )}
                {insight.reasoning && (
                  <p className="text-[10px] font-mono text-gray-600 italic line-clamp-1">
                    {insight.reasoning.slice(0, 90)}
                  </p>
                )}
              </motion.div>
            );
          })}
        </AnimatePresence>

        {allInsights.length === 0 && (
          <div className="py-8 text-center">
            <Brain className="w-8 h-8 text-gray-700 mx-auto mb-2 animate-pulse" />
            <p className="text-xs font-mono text-gray-600 uppercase tracking-widest">Awaiting AI signals...</p>
          </div>
        )}
      </div>
    </div>
  );
}
