import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Lightbulb, Terminal, ChevronRight, Copy, Check } from "lucide-react";
import type { Recommendation } from "../../lib/api";
import { useState } from "react";

const PRIORITY_META: Record<number, { label: string; color: string; badge: string }> = {
  1: { label: "P1 · Critical", color: "text-red-400",    badge: "badge-critical" },
  2: { label: "P2 · High",     color: "text-orange-400", badge: "badge-high"     },
  3: { label: "P3 · Medium",   color: "text-yellow-400", badge: "badge-medium"   },
  4: { label: "P4 · Low",      color: "text-gray-400",   badge: "badge-low"      },
};

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <button
      onClick={copy}
      className="shrink-0 p-1 rounded text-gray-600 hover:text-sentinel-accent hover:bg-sentinel-accent/10 transition-all"
    >
      {copied ? <Check className="w-3 h-3 text-sentinel-success" /> : <Copy className="w-3 h-3" />}
    </button>
  );
}

export default function RecommendationPanel({ items }: { items: Recommendation[] }) {
  return (
    <div className="glass-panel rounded-xl border border-sentinel-700/50 overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-sentinel-700/40 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-yellow-500/10 border border-yellow-500/30 flex items-center justify-center">
            <Lightbulb className="w-4 h-4 text-yellow-400" />
          </div>
          <div>
            <h3 className="text-sm font-display font-semibold text-white">AI Recommendations</h3>
            <p className="text-[9px] font-mono text-gray-500 uppercase tracking-widest mt-0.5">Autonomous remediation</p>
          </div>
        </div>
        <span className="text-[9px] font-mono text-yellow-400/60 uppercase tracking-widest">
          {items.length} actions
        </span>
      </div>

      <div className="p-4 space-y-3">
        <AnimatePresence mode="popLayout">
          {items.slice(0, 6).map((r, i) => {
            const pMeta = PRIORITY_META[r.priority] ?? PRIORITY_META[4];
            return (
              <motion.div
                key={r.id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 8 }}
                transition={{ delay: i * 0.06 }}
                className="glass-panel-light rounded-lg p-3.5 space-y-2 group hover:border-yellow-500/20 transition-all"
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="text-xs font-sans font-semibold text-gray-200 leading-snug flex-1">{r.title}</span>
                  <span className={`shrink-0 text-[9px] px-1.5 py-0.5 rounded font-mono uppercase tracking-wider border ${pMeta.badge}`}>
                    {pMeta.label}
                  </span>
                </div>

                {r.description && (
                  <p className="text-[11px] font-sans text-gray-500 leading-relaxed">{r.description}</p>
                )}

                {r.kubectl_command && (
                  <div className="flex items-center gap-2 bg-black/50 border border-sentinel-700/50 rounded-md px-3 py-2">
                    <Terminal className="w-3 h-3 text-sentinel-accent/60 shrink-0" />
                    <code className="text-[10px] font-mono text-sentinel-accent flex-1 truncate">{r.kubectl_command}</code>
                    <CopyButton text={r.kubectl_command} />
                  </div>
                )}
              </motion.div>
            );
          })}
        </AnimatePresence>

        {items.length === 0 && (
          <div className="py-8 text-center">
            <Lightbulb className="w-8 h-8 text-gray-700 mx-auto mb-2 animate-ai-glow" />
            <p className="text-xs font-mono text-gray-600 uppercase tracking-widest">No recommendations yet</p>
          </div>
        )}
      </div>
    </div>
  );
}
