import { useState } from "react";
import type { WSEvent } from "../../hooks/useWebSocket";

interface Props {
  wsEvents: WSEvent[];
}

export default function AIAssistantPanel({ wsEvents }: Props) {
  const [messages, setMessages] = useState<Array<{ role: string; content: string; timestamp: number }>>([]);

  // Extract NLP assistant responses from WebSocket events
  const nplEvents = wsEvents.filter((e) => e.type === "ai_insight" && e.payload?.agent === "npl_assistant");

  // Add new messages from events
  nplEvents.forEach((event) => {
    const content = event.payload?.findings?.[0] || event.payload?.reasoning || "";
    if (content && !messages.find((m) => m.content === content)) {
      setMessages((prev) => [...prev, { role: "assistant", content, timestamp: Date.now() }]);
    }
  });

  const recentMessages = messages.slice(-5);

  return (
    <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4 space-y-3 flex flex-col h-full">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-sentinel-accent">Infrastructure Assistant</h3>
        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
      </div>

      <div className="flex-1 overflow-y-auto space-y-2 min-h-[200px]">
        {recentMessages.length === 0 ? (
          <p className="text-gray-500 text-xs">Awaiting incident context...</p>
        ) : (
          recentMessages.map((msg, idx) => (
            <div
              key={idx}
              className={`text-xs p-2 rounded ${
                msg.role === "assistant"
                  ? "bg-sentinel-800/50 border-l-2 border-sentinel-500"
                  : "bg-blue-900/20 border-l-2 border-blue-500"
              }`}
            >
              <p className={msg.role === "assistant" ? "text-gray-300" : "text-blue-300"}>{msg.content}</p>
              <p className="text-[10px] text-gray-600 mt-1">
                {new Date(msg.timestamp).toLocaleTimeString()}
              </p>
            </div>
          ))
        )}
      </div>

      <div className="text-[10px] text-gray-600 border-t border-sentinel-700 pt-2">
        <p>Real-time infrastructure insights powered by local AI analysis</p>
      </div>
    </div>
  );
}
