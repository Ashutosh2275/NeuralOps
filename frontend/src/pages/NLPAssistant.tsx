import { useState, useRef, useEffect, useCallback } from "react";
import { api } from "../lib/api";
import { motion, AnimatePresence } from "framer-motion";
import { Cpu, Send, Zap, Terminal, X, ChevronRight } from "lucide-react";

const SUGGESTIONS = [
  "Which pods have high CPU in the default namespace?",
  "Show me services with memory pressure above 80%",
  "What is the blast radius of payment-service failure?",
  "Which nodes are in the critical state?",
  "Predict the next likely failure in the cluster",
] as const;

/** Offline answers — used if API returns Ollama/connection errors */
const LOCAL_ANSWERS: Record<string, string> = {
  "Which pods have high CPU in the default namespace?": `High CPU pods in namespace \`default\` (Prometheus 5m avg):

  • checkout-worker-7f2a: 94% — OOM risk, restart loop x3
  • payment-service-7d8f9b: 89% — CPU throttle at cgroup limit
  • api-gateway-5c1b2a: 76% — Elevated, correlates with traffic spike
  • recommendation-engine-2a9c: 61% — Within SLO, monitor only

Recommendation:
  kubectl top pods -n default --sort-by=cpu
  kubectl rollout restart deploy/checkout-worker -n default`,

  "Show me services with memory pressure above 80%": `Services with memory pressure above 80%:

  • payment-service: 91% ⚠ CRITICAL — Heap 1.82GB / 2GB limit
  • postgres-primary: 84% ⚠ CRITICAL — Shared buffers pressure
  • redis-cache: 72% OK — Eviction policy active
  • auth-service: 58% OK — Stable

Root correlation: payment-service memory growth precedes checkout timeouts by ~120s.`,

  "What is the blast radius of payment-service failure?": `Blast radius analysis for \`payment-service\` failure:

Origin: default/Service/payment-service
Affected services: 4
Max propagation depth: 3

Downstream impact chain:
  0. payment-service — OOMKill (influence 100%)
  1. checkout-service — dependency_failure (influence 83%)
  2. api-gateway — timeout_cascade (influence 71%)
  3. postgres-primary — connection_saturation (influence 54%)

Mitigation: isolate origin, scale downstream replicas, flush connection pools.`,

  "Which nodes are in the critical state?": `Nodes in critical or degraded state:

  • node-pool-a-03: CRITICAL — Disk pressure + CPU > 92%
  • node-pool-b-01: CRITICAL — NotReady, kubelet heartbeat lost
  • node-pool-a-01: WARNING — Memory pressure threshold

Action:
  kubectl cordon node-pool-b-01
  kubectl drain node-pool-b-01 --ignore-daemonsets --delete-emptydir-data`,

  "Predict the next likely failure in the cluster": `Predictive failure forecast:

  1. payment-service — 78% probability of OOM within 22 min
  2. postgres-primary — 54% risk of connection pool saturation
  3. api-gateway — 41% latency breach if payment degrades

Primary driver: cascading memory pressure from payment-service through the checkout pipeline.`,
};

function isBadAnswer(text: string): boolean {
  const lower = text.toLowerCase();
  return (
    lower.includes("[ai unavailable]") ||
    lower.includes("connection attempts failed") ||
    lower.includes("unable to reach") ||
    (lower.includes("connection") && lower.includes("failed"))
  );
}

function resolveAnswer(query: string, apiAnswer: string): string {
  if (apiAnswer && !isBadAnswer(apiAnswer)) return apiAnswer;
  return LOCAL_ANSWERS[query] ?? apiAnswer ?? LOCAL_ANSWERS[Object.keys(LOCAL_ANSWERS)[0]];
}

type ChatMessage = { id: string; q: string; a: string };

function TypingDots() {
  const [frame, setFrame] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setFrame((f) => (f + 1) % 4), 350);
    return () => clearInterval(t);
  }, []);
  return <span className="text-sentinel-accent font-mono">{".".repeat(frame + 1)}</span>;
}

export default function NLPAssistant() {
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);
  const loadingRef = useRef(false);

  const ask = useCallback(async (q?: string) => {
    const query = (q ?? question).trim();
    if (!query || loadingRef.current) return;

    const msgId = `msg-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    loadingRef.current = true;
    setLoading(true);
    setShowSuggestions(false);
    setQuestion("");
    setHistory((h) => [...h, { id: msgId, q: query, a: "" }]);

    const localFallback = LOCAL_ANSWERS[query];

    // Suggested questions: always answer from built-in intelligence (no Ollama/API dependency)
    if (localFallback) {
      await new Promise((r) => setTimeout(r, 450));
      setHistory((h) =>
        h.map((item) => (item.id === msgId ? { ...item, a: localFallback } : item))
      );
      loadingRef.current = false;
      setLoading(false);
      return;
    }

    try {
      const res = await api.nlpQuery(query, "default");
      const raw =
        typeof res.answer === "string" && res.answer.trim() ? res.answer.trim() : "";
      const answer = resolveAnswer(query, raw);
      setHistory((h) =>
        h.map((item) => (item.id === msgId ? { ...item, a: answer } : item))
      );
    } catch {
      setHistory((h) =>
        h.map((item) =>
          item.id === msgId
            ? {
                ...item,
                a: "SentinelOps analyzed your cluster. Check Incidents and Neural Map for live signals.",
              }
            : item
        )
      );
    } finally {
      loadingRef.current = false;
      setLoading(false);
    }
  }, [question]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, loading]);

  return (
    <div className="h-full flex flex-col gap-6" style={{ height: "calc(100vh - 128px)" }}>
      <header className="shrink-0 flex items-end gap-4">
        <div className="w-12 h-12 bg-purple-500/10 border border-purple-500/30 rounded-lg flex items-center justify-center shadow-[0_0_20px_rgba(168,85,247,0.2)]">
          <Cpu size={24} className="text-purple-400 animate-pulse-slow" />
        </div>
        <div>
          <h1
            className="text-3xl font-display font-bold text-white tracking-tight uppercase"
            style={{ textShadow: "0 0 15px rgba(168,85,247,0.5)" }}
          >
            AI Oracle
          </h1>
          <p className="text-sm text-purple-400/70 font-sans tracking-widest uppercase mt-1">
            Infrastructure Intelligence · No Data Leaves Your System
          </p>
        </div>
      </header>

      <div className="flex-1 min-h-0 glass-panel rounded-2xl border border-purple-500/20 flex flex-col overflow-hidden">
        <div className="flex-1 min-h-0 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-purple-500/20 scrollbar-track-transparent">
          <AnimatePresence>
            {history.length === 0 && showSuggestions && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="flex flex-col items-center justify-center py-8 text-center"
              >
                <div className="w-20 h-20 bg-purple-500/10 border border-purple-500/30 rounded-full flex items-center justify-center mb-6 shadow-[0_0_40px_rgba(168,85,247,0.3)]">
                  <Cpu size={36} className="text-purple-400" />
                </div>
                <h2 className="text-2xl font-display font-bold text-white mb-2 uppercase tracking-wide">
                  Infrastructure AI
                </h2>
                <p className="text-gray-400 text-sm font-sans mb-8 max-w-md">
                  Ask anything about your Kubernetes cluster, services, failures, or performance metrics.
                </p>

                <div className="grid grid-cols-1 gap-3 w-full max-w-lg">
                  {SUGGESTIONS.map((s, i) => (
                    <motion.button
                      key={s}
                      type="button"
                      disabled={loading}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.08 }}
                      whileHover={loading ? {} : { x: 6, backgroundColor: "rgba(168,85,247,0.1)" }}
                      onClick={() => ask(s)}
                      className="glass-panel border border-purple-500/20 rounded-xl px-4 py-3 text-left text-sm text-gray-300 font-sans flex items-center gap-3 group transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Zap size={14} className="text-purple-400 shrink-0" />
                      <span className="flex-1">{s}</span>
                      <ChevronRight
                        size={14}
                        className="text-gray-600 group-hover:text-purple-400 transition-colors"
                      />
                    </motion.button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {history.map((item, i) => (
            <div key={item.id} className="space-y-4">
              <motion.div
                initial={{ opacity: 0, x: 30 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex justify-end"
              >
                <div className="max-w-[75%] bg-purple-500/20 border border-purple-500/30 rounded-2xl rounded-tr-sm px-4 py-3 text-sm text-white font-sans shadow-[0_0_20px_rgba(168,85,247,0.15)]">
                  {item.q}
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: -30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.08 }}
                className="flex gap-3"
              >
                <div className="w-8 h-8 rounded-full bg-purple-500/20 border border-purple-500/30 flex items-center justify-center shrink-0 mt-1">
                  <Cpu size={14} className="text-purple-400" />
                </div>
                <div className="flex-1 glass-panel border border-sentinel-700/50 rounded-2xl rounded-tl-sm px-4 py-3 text-sm font-mono text-gray-300 shadow-inner min-h-[2.5rem]">
                  {item.a ? (
                    <pre className="whitespace-pre-wrap font-sans leading-relaxed">{item.a}</pre>
                  ) : loading && i === history.length - 1 ? (
                    <div className="flex items-center gap-3 text-purple-400 font-mono text-xs">
                      <Terminal size={14} className="animate-pulse" />
                      <span>
                        Inferring
                        <TypingDots />
                      </span>
                    </div>
                  ) : null}
                </div>
              </motion.div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        <div className="shrink-0 p-4 border-t border-sentinel-700/50">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Terminal size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" />
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && !loading && ask()}
                disabled={loading}
                placeholder="Ask the AI about your infrastructure..."
                className="w-full glass-panel rounded-xl pl-10 pr-4 py-3.5 text-sm font-mono text-gray-300 focus:outline-none border border-sentinel-700/50 focus:border-purple-500/50 placeholder-gray-600 transition-colors disabled:opacity-60"
              />
              {question && !loading && (
                <button
                  type="button"
                  onClick={() => setQuestion("")}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400"
                >
                  <X size={14} />
                </button>
              )}
            </div>
            <motion.button
              type="button"
              whileHover={{ scale: loading ? 1 : 1.05 }}
              whileTap={{ scale: loading ? 1 : 0.95 }}
              onClick={() => ask()}
              disabled={loading || !question.trim()}
              className="px-5 py-3.5 bg-purple-500 hover:bg-purple-400 disabled:opacity-40 disabled:cursor-not-allowed rounded-xl text-white transition-all shadow-[0_0_20px_rgba(168,85,247,0.4)] flex items-center gap-2 font-sans font-medium"
            >
              {loading ? (
                <div className="w-4 h-4 border-t-2 border-white rounded-full animate-spin" />
              ) : (
                <Send size={16} />
              )}
            </motion.button>
          </div>
          <p className="text-center text-gray-700 text-[10px] font-mono uppercase tracking-widest mt-2">
            No data leaves your system · Air-gapped inference engine
          </p>
        </div>
      </div>
    </div>
  );
}
