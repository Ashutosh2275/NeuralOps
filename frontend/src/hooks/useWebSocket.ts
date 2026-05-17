import { useCallback, useEffect, useRef, useState } from "react";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws";

export interface WSEvent {
  type: string;
  payload: Record<string, unknown>;
}

export function useWebSocket(onMessage?: (event: WSEvent) => void) {
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<WSEvent | null>(null);
  const [events, setEvents] = useState<WSEvent[]>([]);
  const handlerRef = useRef(onMessage);
  handlerRef.current = onMessage;

  const handleMessage = useCallback((event: WSEvent) => {
    setLastEvent(event);
    setEvents((prev) => [event, ...prev].slice(0, 100));
    handlerRef.current?.(event);
  }, []);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (msg) => {
      try {
        const event = JSON.parse(msg.data) as WSEvent;
        if (event.type === "pong") return;
        if (event.type === "batch") {
          const batchedEvents = event.payload.events as WSEvent[];
          batchedEvents.forEach((e) => handleMessage(e));
          return;
        }
        handleMessage(event);
      } catch {
        /* ignore */
      }
    };

    const ping = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send("ping");
    }, 30000);

    return () => {
      clearInterval(ping);
      ws.close();
    };
  }, [handleMessage]);

  return { connected, lastEvent, events };
}
