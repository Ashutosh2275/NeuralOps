import { useState, useRef, useEffect } from "react";
import { api } from "../lib/api";
import { motion, AnimatePresence } from "framer-motion";
import { Cpu, Send, Zap, Terminal, X, ChevronRight } from "lucide-react";

const SUGGESTIONS = [
  "Which pods have high CPU in the default namespace?",
  "Show me services with memory pressure above 80%",
  "What is the blast radius of payment-service failure?",
  "Which nodes are in the critical state?",
  "Predict the next likely failure in the cluster",
];

const TYPING_CHARS = "▌";

function TypingDots() {
  const [frame, setFrame] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setFrame(f => (f + 1) % 4), 350);
    return () => clearInterval(t);
  }, []);
  return <span className="text-sentinel-accent font-mono">{".".repeat(frame + 1)}</span>;
}

export default function NLPAssistant() {
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState<{ q: string; a: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  const ask = async (q?: string) => {
    const query = q ?? question;
    if (!query.trim()) return;
    setLoading(true);
    setShowSuggestions(false);
    setQuestion("");
    setHistory(h => [...h, { q: query, a: "" }]);
    try {
      const res = await api.nlpQuery(query);
      setHistory(h => h.map((item, i) => i === h.length - 1 ? { ...item, a: res.answer } : item));
    } catch {
      setHistory(h => h.map((item, i) => i === h.length - 1 ? { ...item, a: "⚠ AI service unreachable. Ensure Ollama is running with `ollama serve`." } : item));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, loading]);

  return (
    <div className="h-full flex flex-col gap-6">
      {/* Header */}
      <header className="flex items-end gap-4">
        <div className="w-12 h-12 bg-purple-500/10 border border-purple-500/30 rounded-lg flex items-center justify-center shadow-[0_0_20px_rgba(168,85,247,0.2)]">
          <Cpu size={24} className="text-purple-400 animate-pulse-slow" />
        </div>
        <div>
          <h1 className="text-3xl font-display font-bold text-white tracking-tight uppercase" style={{ textShadow: "0 0 15px rgba(168,85,247,0.5)" }}>
            AI Oracle
          </h1>
          <p className="text-sm text-purple-400/70 font-sans tracking-widest uppercase mt-1">
            Infrastructure Intelligence · No Data Leaves Your System
          </p>
        </div>
      </header>

      {/* Chat window */}
      <div className="flex-1 glass-panel rounded-2xl border border-purple-500/20 flex flex-col overflow-hidden">
        {/* Chat messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Welcome state */}
          <AnimatePresence>
            {history.length === 0 && showSuggestions && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="flex flex-col items-center justify-center py-12 text-center"
              >
                <div className="w-20 h-20 bg-purple-500/10 border border-purple-500/30 rounded-full flex items-center justify-center mb-6 shadow-[0_0_40px_rgba(168,85,247,0.3)]">
                  <Cpu size={36} className="text-purple-400" />
                </div>
                <h2 className="text-2xl font-display font-bold text-white mb-2 uppercase tracking-wide">Infrastructure AI</h2>
                <p className="text-gray-400 text-sm font-sans mb-8 max-w-md">Ask anything about your Kubernetes cluster, services, failures, or performance metrics.</p>

                <div className="grid grid-cols-1 gap-3 w-full max-w-lg">
                  {SUGGESTIONS.map((s, i) => (
                    <motion.button
                      key={i}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                      whileHover={{ x: 6, backgroundColor: "rgba(168,85,247,0.1)" }}
                      onClick={() => ask(s)}
                      className="glass-panel border border-purple-500/20 rounded-xl px-4 py-3 text-left text-sm text-gray-300 font-sans flex items-center gap-3 group transition-all"
                    >
                      <Zap size={14} className="text-purple-400 shrink-0" />
                      <span className="flex-1">{s}</span>
                      <ChevronRight size={14} className="text-gray-600 group-hover:text-purple-400 transition-colors" />
                    </motion.button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Messages */}
          {history.map((item, i) => (
            <div key={i} className="space-y-4">
              {/* Question bubble */}
              <motion.div
                initial={{ opacity: 0, x: 30 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex justify-end"
              >
                <div className="max-w-[75%] bg-purple-500/20 border border-purple-500/30 rounded-2xl rounded-tr-sm px-4 py-3 text-sm text-white font-sans shadow-[0_0_20px_rgba(168,85,247,0.15)]">
                  {item.q}
                </div>
              </motion.div>

              {/* Answer bubble */}
              <motion.div
                initial={{ opacity: 0, x: -30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
                className="flex gap-3"
              >
                <div className="w-8 h-8 rounded-full bg-purple-500/20 border border-purple-500/30 flex items-center justify-center shrink-0 mt-1">
                  <Cpu size={14} className="text-purple-400" />
                </div>
                <div className="flex-1 glass-panel border border-sentinel-700/50 rounded-2xl rounded-tl-sm px-4 py-3 text-sm font-mono text-gray-300 shadow-inner">
                  {item.a ? (
                    <pre className="whitespace-pre-wrap font-sans leading-relaxed">{item.a}</pre>
                  ) : (
                    loading && i === history.length - 1 ? (
                      <div className="flex items-center gap-3 text-purple-400 font-mono text-xs">
                        <Terminal size={14} className="animate-pulse" />
                        <span>Inferring<TypingDots /></span>
                      </div>
                    ) : null
                  )}
                </div>
              </motion.div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        {/* Input area */}
        <div className="p-4 border-t border-sentinel-700/50">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Terminal size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" />
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && ask()}
                placeholder="Ask the AI about your infrastructure..."
                className="w-full glass-panel rounded-xl pl-10 pr-4 py-3.5 text-sm font-mono text-gray-300 focus:outline-none border border-sentinel-700/50 focus:border-purple-500/50 placeholder-gray-600 transition-colors"
              />
              {question && (
                <button onClick={() => setQuestion("")} className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400">
                  <X size={14} />
                </button>
              )}
            </div>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => ask()}
              disabled={loading || !question.trim()}
              className="px-5 py-3.5 bg-purple-500 hover:bg-purple-400 disabled:opacity-40 disabled:cursor-not-allowed rounded-xl text-white transition-all shadow-[0_0_20px_rgba(168,85,247,0.4)] flex items-center gap-2 font-sans font-medium"
            >
              {loading ? <div className="w-4 h-4 border-t-2 border-white rounded-full animate-spin" /> : <Send size={16} />}
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
