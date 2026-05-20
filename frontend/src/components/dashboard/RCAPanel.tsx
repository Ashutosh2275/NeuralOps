import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Target, Link as LinkIcon, GitBranch, ArrowRight } from "lucide-react";

interface RCAData {
  root_cause?: string;
  root_service?: string;
  confidence?: number;
  cascade_chain?: Array<{ service: string; order: number; failure_mode?: string; influence?: number }>;
  affected_count?: number;
  propagation_depth?: number;
  title?: string;
}

interface Props {
  rca: RCAData | null;
  rawEvents?: any[];
}

function InfluenceBar({ value }: { value: number }) {
  const pct = value * 100;
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1 bg-sentinel-900 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="h-full rounded-full"
          style={{
            background: pct > 80 ? "#ef4444" : pct > 60 ? "#f59e0b" : "#22d3ee",
            boxShadow: `0 0 4px ${pct > 80 ? "#ef4444" : pct > 60 ? "#f59e0b" : "#22d3ee"}`,
          }}
        />
      </div>
      <span className="text-[9px] font-mono text-orange-400 w-7 text-right tabular-nums">{pct.toFixed(0)}%</span>
    </div>
  );
}

export default function RCAPanel({ rca }: Props) {
  if (!rca || (!rca.root_cause && !rca.root_service)) {
    return (
      <div className="glass-panel rounded-xl border border-sentinel-700/50 p-5">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center">
            <Target className="w-4 h-4 text-purple-400" />
          </div>
          <h3 className="text-sm font-display font-semibold text-white">Root Cause Analysis</h3>
        </div>
        <p className="text-xs font-mono text-gray-600 uppercase tracking-widest">Select an incident to view RCA</p>
      </div>
    );
  }

  const confidence = (rca.confidence ?? 0) * 100;
  const cascade    = rca.cascade_chain ?? [];
  const confColor  = confidence >= 80 ? "#10b981" : confidence >= 60 ? "#f59e0b" : "#ef4444";

  return (
    <div className="glass-panel rounded-xl border border-purple-500/25 overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-sentinel-700/40 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center">
            <Target className="w-4 h-4 text-purple-400" />
          </div>
          <div>
            <h3 className="text-sm font-display font-semibold text-white">Root Cause Analysis</h3>
            {rca.root_service && (
              <p className="text-[9px] font-mono text-sentinel-accent/60 uppercase tracking-widest mt-0.5">
                Origin: {rca.root_service}
              </p>
            )}
          </div>
        </div>
        {/* Confidence ring */}
        <div className="flex flex-col items-end">
          <span className="text-lg font-display font-bold tabular-nums" style={{ color: confColor }}>
            {confidence.toFixed(0)}%
          </span>
          <span className="text-[9px] font-mono text-gray-600 uppercase tracking-widest">confidence</span>
        </div>
      </div>

      <div className="p-5 space-y-4">
        {/* Primary cause */}
        {rca.root_cause && (
          <motion.div
            layout
            initial={{ opacity: 0, y: 15, filter: "blur(5px)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
            className="rounded-lg bg-sentinel-accent/5 border-l-2 border-sentinel-accent px-4 py-3"
          >
            <p className="text-[9px] font-mono text-sentinel-accent/50 uppercase tracking-widest mb-1">Primary Cause</p>
            <p className="text-sm font-sans text-gray-200 leading-relaxed">{rca.root_cause}</p>
          </motion.div>
        )}

        {/* Cascade chain */}
        {cascade.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 mb-3">
              <GitBranch className="w-3.5 h-3.5 text-gray-500" />
              <span className="text-[10px] font-mono text-gray-400 uppercase tracking-widest">
                Cascade Chain ({cascade.length} hops)
              </span>
            </div>
            <div className="space-y-2.5">
              {cascade.map((c, i) => (
                <motion.div
                  key={i}
                  layout
                  initial={{ opacity: 0, x: -15, filter: "blur(4px)" }}
                  animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
                  transition={{ type: "spring", stiffness: 350, damping: 25, delay: i * 0.08 }}
                  className="glass-panel-light rounded-lg px-3 py-2"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-red-500/20 border border-red-500/30 flex items-center justify-center text-[9px] font-mono text-red-400 shrink-0">
                        {c.order}
                      </span>
                      <span className="text-xs font-mono text-gray-200">{c.service}</span>
                      {c.failure_mode && (
                        <span className="text-[9px] font-mono text-gray-600">({c.failure_mode})</span>
                      )}
                    </div>
                  </div>
                  {c.influence != null && <InfluenceBar value={c.influence} />}
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Meta */}
        {(rca.affected_count || rca.propagation_depth) && (
          <div className="grid grid-cols-2 gap-3 pt-2 border-t border-sentinel-700/30">
            {rca.affected_count && (
              <div className="glass-panel-light rounded-lg p-3 text-center">
                <p className="text-lg font-display font-bold text-sentinel-danger">{rca.affected_count}</p>
                <p className="text-[9px] font-mono text-gray-600 uppercase tracking-widest mt-0.5">Services Affected</p>
              </div>
            )}
            {rca.propagation_depth && (
              <div className="glass-panel-light rounded-lg p-3 text-center">
                <p className="text-lg font-display font-bold text-orange-400">{rca.propagation_depth}</p>
                <p className="text-[9px] font-mono text-gray-600 uppercase tracking-widest mt-0.5">Cascade Depth</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
