import { useState } from "react";
import { api } from "../lib/api";

export default function NLPAssistant() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  const ask = async () => {
    if (!question.trim()) return;
    setLoading(true);
    try {
      const res = await api.nlpQuery(question);
      setAnswer(res.answer);
    } catch {
      setAnswer("Failed to reach AI service. Ensure Ollama is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl space-y-4">
      <h2 className="font-display text-2xl font-bold">Infrastructure Assistant</h2>
      <p className="text-gray-500 text-sm">Ask questions about your cluster in natural language</p>

      <div className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && ask()}
          placeholder="Which pods have high CPU in the default namespace?"
          className="flex-1 bg-sentinel-900 border border-sentinel-700 rounded px-4 py-2 text-sm focus:outline-none focus:border-sentinel-accent"
        />
        <button
          onClick={ask}
          disabled={loading}
          className="bg-sentinel-500 hover:bg-sentinel-400 px-4 py-2 rounded text-sm font-medium disabled:opacity-50"
        >
          {loading ? "..." : "Ask"}
        </button>
      </div>

      {answer && (
        <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4">
          <pre className="text-sm text-gray-300 whitespace-pre-wrap font-sans">{answer}</pre>
        </div>
      )}
    </div>
  );
}
