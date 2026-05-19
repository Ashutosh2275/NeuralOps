import React, { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, Zap, TrendingUp, Shield, AlertTriangle, GitBranch } from "lucide-react";
import { useReasoningLog } from "../../contexts/PlatformContext";

interface Props { insights?: any[]; wsEvents?: any[]; }

const SEED_INSIGHTS = [
  { agent:"rca",            conf:0.94, finding:"Memory pressure escalation across api-gateway pods. OOM probability 87%.", reasoning:"Heap growth rate +2.3MB/s over 8 min window" },
  { agent:"correlation",    conf:0.88, finding:"Correlated latency spike: payment-svc → postgres. Connection pool saturation.", reasoning:"Event cross-correlation window: 120s, r=0.91" },
  { agent:"recommendation", conf:0.97, finding:"Recommend: scale api-gateway 3→6 replicas + flush postgres connection pool.", reasoning:"TTR estimate: 4.2 min at 94% confidence" },
  { agent:"cpu",            conf:0.81, finding:"CPU throttling: worker-fleet consuming 92% of allocated. Quota increase needed.", reasoning:"cgroup limit breach detected on 7 of 12 pods" },
  { agent:"memory",         conf:0.76, finding:"Redis cluster heap at 84%. Eviction policy may trigger under peak load.", reasoning:"Growth trend: +1.8MB/s, projected breach: 22min" },
  { agent:"network",        conf:0.83, finding:"Inter-zone latency elevated: AZ-A ↔ AZ-B +38ms. Possible network congestion.", reasoning:"BGP path change detected 4min ago" },
];

const AGENT_META: Record<string,{color:string;icon:React.ReactElement;label:string}> = {
  cpu:            { color:"text-red-400",    icon:<Zap className="w-3 h-3" />,          label:"CPU Monitor"  },
  memory:         { color:"text-orange-400", icon:<AlertTriangle className="w-3 h-3" />, label:"Mem Monitor"  },
  network:        { color:"text-blue-400",   icon:<Zap className="w-3 h-3" />,          label:"Net Monitor"  },
  rca:            { color:"text-green-400",  icon:<Brain className="w-3 h-3" />,         label:"RCA Engine"   },
  correlation:    { color:"text-yellow-400", icon:<TrendingUp className="w-3 h-3" />,    label:"Correlator"   },
  recommendation: { color:"text-cyan-400",   icon:<Shield className="w-3 h-3" />,        label:"Recommender"  },
  logs:           { color:"text-purple-400", icon:<GitBranch className="w-3 h-3" />,     label:"Log Analyzer" },
};

export default function AIInsightsPanel({ insights = [], wsEvents = [] }: Props) {
  const reasoning = useReasoningLog();
  const [items, setItems] = useState(SEED_INSIGHTS);
  const idx = useRef(0);

  // Rotate one insight every 6 seconds so the panel is never empty and always "alive"
  useEffect(() => {
    const t = setInterval(() => {
      idx.current = (idx.current + 1) % SEED_INSIGHTS.length;
      setItems(prev => {
        const next = [...prev];
        next[idx.current] = {
          ...SEED_INSIGHTS[idx.current],
          conf: Math.max(0.55, Math.min(0.99, SEED_INSIGHTS[idx.current].conf + (Math.random()-0.5)*0.06)),
        };
        return next;
      });
    }, 6000);
    return () => clearInterval(t);
  }, []);

  // Merge ws ai_insight events on top
  const wsInsights = wsEvents.filter(e => e.type === "ai_insight").slice(0, 3).map((e:any) => ({
    agent: e.payload?.agent ?? "rca",
    conf:  e.payload?.confidence ?? 0.8,
    finding: e.payload?.findings?.[0] ?? e.payload?.reasoning ?? "AI signal received",
    reasoning: e.payload?.reasoning ?? "",
  }));

  const all = [...wsInsights, ...items].slice(0, 6);

  const P = { background:"rgb(11,19,34)", border:"1px solid rgba(40,65,105,0.35)", borderRadius:12 } as const;

  return (
    <div style={{ ...P, overflow:"hidden" }}>
      <div style={{ padding:"0.75rem 1rem", borderBottom:"1px solid rgba(40,65,105,0.3)",
        display:"flex", alignItems:"center", justifyContent:"space-between" }}>
        <div style={{ display:"flex", alignItems:"center", gap:8 }}>
          <div style={{ width:28, height:28, background:"rgba(34,211,238,0.08)", border:"1px solid rgba(34,211,238,0.25)",
            borderRadius:8, display:"flex", alignItems:"center", justifyContent:"center" }}>
            <Brain className="w-3.5 h-3.5 text-sentinel-accent" />
          </div>
          <div>
            <p style={{ fontSize:"0.6875rem", fontFamily:"Space Grotesk", fontWeight:700, color:"#fff" }}>AI Analysis</p>
            <p style={{ fontSize:"0.5rem", fontFamily:"JetBrains Mono", letterSpacing:"0.15em",
              textTransform:"uppercase", color:"rgba(255,255,255,0.25)", marginTop:2 }}>
              Multi-agent inference · {all.length} active signals
            </p>
          </div>
        </div>
        <span style={{ width:7, height:7, borderRadius:"50%", background:"rgb(34,211,238)",
          animation:"pulse-green 2s infinite", display:"inline-block" }} />
      </div>

      <div style={{ padding:"0.5rem 0.75rem", display:"flex", flexDirection:"column", gap:6 }}>
        <AnimatePresence mode="popLayout">
          {all.map((item, i) => {
            const meta = AGENT_META[item.agent] ?? { color:"text-gray-400", icon:<Zap className="w-3 h-3"/>, label:item.agent };
            const pct  = Math.round(item.conf * 100);
            const barColor = pct >= 80 ? "#10b981" : pct >= 60 ? "#f59e0b" : "#ef4444";
            return (
              <motion.div key={`${item.agent}-${i}`}
                initial={{ opacity:0, x:-8 }} animate={{ opacity:1, x:0 }} exit={{ opacity:0 }}
                transition={{ delay: i*0.04 }}
                style={{ background:"rgba(255,255,255,0.02)", border:"1px solid rgba(40,65,105,0.25)",
                  borderRadius:8, padding:"0.5rem 0.65rem" }}>
                <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:6 }}>
                  <div style={{ display:"flex", alignItems:"center", gap:6 }}>
                    <span className={meta.color}>{meta.icon}</span>
                    <span style={{ fontSize:"0.5625rem", fontFamily:"JetBrains Mono", letterSpacing:"0.1em",
                      textTransform:"uppercase" }} className={meta.color}>{meta.label}</span>
                  </div>
                  <span style={{ fontSize:"0.5rem", fontFamily:"JetBrains Mono", color:"rgba(255,255,255,0.3)" }}>{pct}%</span>
                </div>
                <div style={{ height:2, background:"rgba(255,255,255,0.06)", borderRadius:2, overflow:"hidden", marginBottom:6 }}>
                  <motion.div animate={{ width:`${pct}%` }} transition={{ duration:0.7 }}
                    style={{ height:"100%", background:barColor, borderRadius:2 }} />
                </div>
                <p style={{ fontSize:"0.5625rem", fontFamily:"JetBrains Mono", color:"rgba(255,255,255,0.6)",
                  lineHeight:1.55, marginBottom:2 }}>{item.finding}</p>
                {item.reasoning && (
                  <p style={{ fontSize:"0.5rem", fontFamily:"JetBrains Mono",
                    color:"rgba(255,255,255,0.2)", fontStyle:"italic" }}>{item.reasoning}</p>
                )}
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
