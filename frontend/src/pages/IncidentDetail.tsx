import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api";
import { useWebSocket } from "../hooks/useWebSocket";
import AIInsightsPanel from "../components/dashboard/AIInsightsPanel";
import RCAPanel from "../components/dashboard/RCAPanel";
import RecommendationPanel from "../components/dashboard/RecommendationPanel";
import { motion } from "framer-motion";
import { ArrowLeft, Film, ShieldAlert, Activity, CheckCircle, Clock, Zap, Target } from "lucide-react";

const TIMELINE_ICONS: Record<string, React.ReactElement> = {
  anomaly_detected:    <Zap size={16} className="text-yellow-400" />,
  ai_triage:           <Activity size={16} className="text-blue-400" />,
  rca_complete:        <Target size={16} className="text-purple-400" />,
  blast_radius_mapped: <ShieldAlert size={16} className="text-red-400" />,
  remediation_started: <Zap size={16} className="text-orange-400" />,
  mitigated:           <CheckCircle size={16} className="text-green-400" />,
};

const SEV_COLOR: Record<string, string> = {
  critical: "text-red-400",
  high: "text-orange-400",
  medium: "text-yellow-400",
  low: "text-green-400",
};

export default function IncidentDetail() {
  const { id } = useParams<{ id: string }>();
  const [incident, setIncident] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const { events } = useWebSocket();
  const [insights, setInsights] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);

  useEffect(() => {
    if (id) api.incident(id).then(d => { setIncident(d); setLoading(false); }).catch(() => { setIncident(null); setLoading(false); });
  }, [id]);

  useEffect(() => {
    const aiInsights = events.filter(e => e.type === "ai_insight").map(e => ({
      agent: e.payload?.agent || "unknown",
      findings: e.payload?.findings || [],
      confidence: e.payload?.confidence || 0,
      reasoning: e.payload?.reasoning || "",
    }));
    setInsights(aiInsights);
    setRecommendations(events.filter(e => e.type === "recommendations").flatMap(e => e.payload || []));
  }, [events]);

  if (loading) return (
    <div className="h-full flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-10 h-10 rounded-full border-t-2 border-sentinel-accent animate-spin" />
        <span className="text-sentinel-accent font-mono text-xs uppercase tracking-widest animate-pulse">Fetching Incident Data...</span>
      </div>
    </div>
  );

  if (!incident) return (
    <div className="h-full flex items-center justify-center">
      <div className="text-center">
        <ShieldAlert size={40} className="text-gray-700 mx-auto mb-3" />
        <p className="text-gray-500 font-mono text-sm">Incident record not found.</p>
        <Link to="/incidents" className="text-sentinel-accent text-sm mt-4 block hover:underline">← Back to Registry</Link>
      </div>
    </div>
  );

  const timeline = (incident.timeline as { timestamp: string; title: string; type: string }[]) ?? [];
  const severity = String(incident.severity ?? "low");
  const cascadeChain = (incident.cascade_chain as any[]) ?? [];
  const affectedServices = (incident.affected_services as string[]) ?? [];

  return (
    <div className="h-full flex flex-col gap-6">
      {/* Back nav */}
      <div className="flex items-center gap-3">
        <Link to="/incidents">
          <motion.div whileHover={{ x: -3 }} className="flex items-center gap-2 text-gray-400 hover:text-white text-sm font-mono uppercase tracking-widest transition-colors">
            <ArrowLeft size={16} /> Back to Registry
          </motion.div>
        </Link>
        <div className="flex-1" />
        <Link to={`/replay/${id}`}>
          <motion.div
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            className="flex items-center gap-2 px-4 py-2 bg-purple-500/20 border border-purple-500/40 rounded-lg text-purple-400 text-sm font-mono uppercase tracking-widest hover:bg-purple-500/30 transition-all"
          >
            <Film size={14} /> Cinematic Replay
          </motion.div>
        </Link>
      </div>

      {/* Incident header card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel rounded-2xl p-6 border-l-4 border-red-500 bg-red-500/5 shadow-[0_0_30px_rgba(239,68,68,0.1)]"
      >
        <div className="flex items-start justify-between gap-4 mb-4">
          <h1 className="text-2xl font-display font-bold text-white">{String(incident.title)}</h1>
          <span className={`shrink-0 text-sm px-3 py-1 rounded-lg border font-mono uppercase tracking-widest bg-red-500/20 border-red-500/40 ${SEV_COLOR[severity] ?? "text-gray-400"}`}>
            {severity}
          </span>
        </div>

        <div className="flex flex-wrap gap-6 text-xs font-mono">
          {[
            ["Root Service", String(incident.root_service ?? "—"), "text-sentinel-accent"],
            ["Status", String(incident.status ?? "—"), "text-blue-400"],
            ["Confidence", incident.confidence_score ? `${((incident.confidence_score as number) * 100).toFixed(0)}%` : "—", "text-green-400"],
            ["Detected", incident.started_at ? new Date(incident.started_at as string).toLocaleString() : "—", "text-gray-300"],
          ].map(([lbl, val, color]) => (
            <div key={lbl} className="flex flex-col gap-1">
              <span className="text-gray-600 uppercase tracking-widest text-[10px]">{lbl}</span>
              <span className={color}>{val}</span>
            </div>
          ))}
        </div>

        {!!incident.root_cause && (
          <div className="mt-4 pt-4 border-t border-white/10">
            <span className="text-[10px] text-gray-600 font-mono uppercase tracking-widest">Root Cause Analysis</span>
            <p className="text-gray-300 text-sm font-sans mt-1 leading-relaxed">{String(incident.root_cause)}</p>
          </div>
        )}
      </motion.div>

      <div className="grid grid-cols-12 gap-6 flex-1 min-h-0">
        {/* Left: Timeline + Cascade */}
        <div className="col-span-4 flex flex-col gap-6 overflow-y-auto">
          {/* Timeline */}
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }} className="glass-panel rounded-xl p-5">
            <h3 className="text-xs font-display text-sentinel-accent uppercase tracking-widest mb-4">Event Timeline</h3>
            <div className="relative">
              <div className="absolute left-3 top-0 bottom-0 w-px bg-gradient-to-b from-sentinel-accent/50 to-transparent" />
              <div className="space-y-4 pl-8">
                {timeline.map((t, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.08 }}
                    className="relative"
                  >
                    <div className="absolute -left-5 top-1 w-2 h-2 rounded-full bg-sentinel-accent shadow-[0_0_8px_rgba(34,211,238,0.8)]" />
                    <div className="flex items-start gap-2">
                      {TIMELINE_ICONS[t.type] ?? <Clock size={16} className="text-gray-500" />}
                      <div>
                        <p className="text-sm text-white font-sans font-medium">{t.title}</p>
                        <p className="text-[10px] text-gray-500 font-mono mt-0.5">{t.timestamp}</p>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Cascade chain */}
          {cascadeChain.length > 0 && (
            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }} className="glass-panel rounded-xl p-5">
              <h3 className="text-xs font-display text-red-400 uppercase tracking-widest mb-4">Cascade Chain</h3>
              <div className="space-y-2">
                {cascadeChain.map((step: any, i: number) => (
                  <div key={i} className="flex items-center gap-3">
                    <span className="w-5 h-5 rounded-full bg-red-500/20 border border-red-500/40 flex items-center justify-center text-[10px] text-red-400 font-mono shrink-0">{step.order ?? i}</span>
                    <div className="flex-1">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-white font-sans">{step.service}</span>
                        <span className="text-[10px] text-red-400 font-mono">{step.failure_mode}</span>
                      </div>
                      <div className="mt-1 h-1 bg-sentinel-950 rounded overflow-hidden">
                        <div className="h-full bg-red-500 rounded" style={{ width: `${(step.influence ?? 0.5) * 100}%` }} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Affected services */}
          {affectedServices.length > 0 && (
            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }} className="glass-panel rounded-xl p-5">
              <h3 className="text-xs font-display text-orange-400 uppercase tracking-widest mb-3">Affected Services</h3>
              <div className="flex flex-wrap gap-2">
                {affectedServices.map((svc, i) => (
                  <span key={i} className="text-xs font-mono px-2.5 py-1 rounded-lg bg-orange-500/15 border border-orange-500/30 text-orange-300">{svc}</span>
                ))}
              </div>
            </motion.div>
          )}
        </div>

        {/* Right: AI panels */}
        <div className="col-span-8 flex flex-col gap-6 overflow-y-auto">
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}>
            <RCAPanel rca={incident as any} />
          </motion.div>
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15 }}>
            <RecommendationPanel items={recommendations} />
          </motion.div>
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
            <AIInsightsPanel insights={insights} wsEvents={events} />
          </motion.div>
        </div>
      </div>
    </div>
  );
}
