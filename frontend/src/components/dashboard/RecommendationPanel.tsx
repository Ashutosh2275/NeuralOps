import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Lightbulb, Terminal, Copy, Check } from "lucide-react";
import type { Recommendation } from "../../lib/api";

const PRIORITY_META: Record<number,{label:string;badge:string}> = {
  1: { label:"P1 · Critical", badge:"badge-critical" },
  2: { label:"P2 · High",     badge:"badge-high"     },
  3: { label:"P3 · Medium",   badge:"badge-medium"   },
  4: { label:"P4 · Low",      badge:"badge-low"      },
};

const SEED_RECS: Recommendation[] = [
  { id:"s1", priority:1, action_type:"scale",     confidence:0.94, title:"Scale api-gateway: 3 → 6 replicas to absorb traffic spike",      description:"Memory OOM predicted in 8min. Horizontal scale restores SLA within 90s.", kubectl_command:"kubectl scale deploy api-gateway --replicas=6 -n production" },
  { id:"s2", priority:1, action_type:"exec",      confidence:0.91, title:"Flush postgres-main connection pool (512/512 exhausted)",        description:"Connection exhaustion blocking payment-svc. Pool flush recovers capacity.", kubectl_command:"kubectl exec -n production deploy/postgres-main -- pg_ctl reload" },
  { id:"s3", priority:2, action_type:"delete",    confidence:0.87, title:"Evict degraded pod: payment-svc-7d8f9b (OOMKill loop)",         description:"Pod in CrashLoopBackOff. Evict to allow clean reschedule.",                kubectl_command:"kubectl delete pod payment-svc-7d8f9b -n production" },
  { id:"s4", priority:2, action_type:"annotate",  confidence:0.83, title:"Apply circuit breaker to auth-service upstream",                 description:"Upstream timeout cascade detected. Open circuit breaker prevents propagation.", kubectl_command:"kubectl annotate svc auth-service circuit-breaker=open" },
  { id:"s5", priority:3, action_type:"resources", confidence:0.78, title:"Increase redis-cluster heap limit from 4GB → 6GB",              description:"Heap at 84%. Eviction events expected at 90%+. Expand before peak load.", kubectl_command:"kubectl set resources deploy redis-cluster --limits=memory=6Gi" },
];

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button onClick={() => { navigator.clipboard.writeText(text).catch(()=>{}); setCopied(true); setTimeout(()=>setCopied(false),1500); }}
      style={{ flexShrink:0, background:"none", border:"none", cursor:"pointer", padding:4, borderRadius:4, color:"rgba(255,255,255,0.3)" }}
      className="hover:text-sentinel-accent transition-colors">
      {copied ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
    </button>
  );
}

const P = { background:"rgb(11,19,34)", border:"1px solid rgba(40,65,105,0.35)", borderRadius:12 } as const;

export default function RecommendationPanel({ items = [] }: { items?: Recommendation[] }) {
  const all = [...items, ...SEED_RECS].slice(0, 6);
  return (
    <div style={{ ...P, overflow:"hidden" }}>
      <div style={{ padding:"0.75rem 1rem", borderBottom:"1px solid rgba(40,65,105,0.3)",
        display:"flex", alignItems:"center", justifyContent:"space-between" }}>
        <div style={{ display:"flex", alignItems:"center", gap:8 }}>
          <div style={{ width:28, height:28, background:"rgba(234,179,8,0.08)", border:"1px solid rgba(234,179,8,0.25)",
            borderRadius:8, display:"flex", alignItems:"center", justifyContent:"center" }}>
            <Lightbulb className="w-3.5 h-3.5 text-yellow-400" />
          </div>
          <div>
            <p style={{ fontSize:"0.6875rem", fontFamily:"Space Grotesk", fontWeight:700, color:"#fff" }}>AI Recommendations</p>
            <p style={{ fontSize:"0.5rem", fontFamily:"JetBrains Mono", letterSpacing:"0.15em",
              textTransform:"uppercase", color:"rgba(255,255,255,0.25)", marginTop:2 }}>
              Autonomous remediation · {all.length} actions
            </p>
          </div>
        </div>
      </div>
      <div style={{ padding:"0.5rem 0.75rem", display:"flex", flexDirection:"column", gap:6 }}>
        <AnimatePresence mode="popLayout">
          {all.map((r, i) => {
            const pMeta = PRIORITY_META[r.priority] ?? PRIORITY_META[4];
            return (
              <motion.div key={r.id} initial={{ opacity:0, x:-8 }} animate={{ opacity:1, x:0 }}
                exit={{ opacity:0 }} transition={{ delay:i*0.05 }}
                style={{ background:"rgba(255,255,255,0.02)", border:"1px solid rgba(40,65,105,0.25)", borderRadius:8, padding:"0.55rem 0.65rem" }}>
                <div style={{ display:"flex", alignItems:"flex-start", justifyContent:"space-between", gap:8, marginBottom:4 }}>
                  <span style={{ fontSize:"0.5625rem", fontFamily:"Space Grotesk", fontWeight:600, color:"rgba(255,255,255,0.75)", lineHeight:1.45, flex:1 }}>{r.title}</span>
                  <span className={pMeta.badge} style={{ flexShrink:0, fontSize:"0.45rem", padding:"1px 5px", borderRadius:4,
                    fontFamily:"JetBrains Mono", textTransform:"uppercase", letterSpacing:"0.1em", whiteSpace:"nowrap" }}>
                    {pMeta.label}
                  </span>
                </div>
                {r.description && (
                  <p style={{ fontSize:"0.5rem", fontFamily:"JetBrains Mono", color:"rgba(255,255,255,0.3)", lineHeight:1.5, marginBottom:r.kubectl_command?6:0 }}>
                    {r.description}
                  </p>
                )}
                {r.kubectl_command && (
                  <div style={{ display:"flex", alignItems:"center", gap:6, background:"rgba(0,0,0,0.4)", border:"1px solid rgba(40,65,105,0.3)", borderRadius:6, padding:"0.3rem 0.5rem" }}>
                    <Terminal className="w-3 h-3 text-sentinel-accent" style={{ flexShrink:0, opacity:0.6 }} />
                    <code style={{ fontSize:"0.5rem", fontFamily:"JetBrains Mono", color:"rgb(34,211,238)", flex:1, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>
                      {r.kubectl_command}
                    </code>
                    <CopyButton text={r.kubectl_command} />
                  </div>
                )}
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
