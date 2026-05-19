/**
 * PlatformContext — Single global source of truth for the entire NeuralOps platform.
 *
 * ALL pages consume from this context. This ensures:
 * - Consistent incident counts across every page
 * - Persistent WebSocket-driven AI reasoning stream
 * - Shared topology state that never reinitializes on navigation
 * - Shared analytics metrics
 * - Universal infrastructure health
 */
import React, {
  createContext, useCallback, useContext, useEffect,
  useReducer, useRef, useState,
} from "react";
import { api, IncidentSummary, TopologyGraph } from "../lib/api";

// ── Types ─────────────────────────────────────────────────────────────
export interface ReasoningEntry {
  id: string;
  agent: string;
  text: string;
  ts: string;
  kind: "info" | "warn" | "success" | "critical";
}

export interface LiveMetrics {
  cpuAvg: number;
  memUsage: number;
  netMbps: number;
  errorRate: number;
  p99Latency: number;
  slaPercent: number;
}

export interface PlatformState {
  // Infrastructure
  incidents: IncidentSummary[];
  topology: TopologyGraph | null;
  health: string;
  // AI Engine
  reasoningLog: ReasoningEntry[];
  agentActivity: Record<string, "idle" | "active" | "thinking">;
  gpuUtil: number;
  // Live metrics
  metrics: LiveMetrics;
  // WebSocket
  wsConnected: boolean;
  wsEventCount: number;
  criticalCount: number;
}

const INITIAL_METRICS: LiveMetrics = {
  cpuAvg: 67, memUsage: 74, netMbps: 892, errorRate: 23,
  p99Latency: 0.7, slaPercent: 99.1,
};

const INITIAL_STATE: PlatformState = {
  incidents: [], topology: null, health: "checking",
  reasoningLog: [], agentActivity: {}, gpuUtil: 72,
  metrics: INITIAL_METRICS,
  wsConnected: false, wsEventCount: 0, criticalCount: 0,
};

// ── Actions ───────────────────────────────────────────────────────────
type Action =
  | { type: "SET_INCIDENTS"; payload: IncidentSummary[] }
  | { type: "SET_TOPOLOGY"; payload: TopologyGraph }
  | { type: "SET_HEALTH"; payload: string }
  | { type: "ADD_REASONING"; payload: ReasoningEntry }
  | { type: "SET_AGENT"; payload: { id: string; status: "idle" | "active" | "thinking" } }
  | { type: "SET_GPU"; payload: number }
  | { type: "SET_METRICS"; payload: Partial<LiveMetrics> }
  | { type: "SET_WS"; payload: { connected: boolean } }
  | { type: "INC_WS_EVENT" };

function reducer(state: PlatformState, action: Action): PlatformState {
  switch (action.type) {
    case "SET_INCIDENTS":
      return {
        ...state,
        incidents: action.payload,
        criticalCount: action.payload.filter(i => i.severity === "critical").length,
      };
    case "SET_TOPOLOGY":    return { ...state, topology: action.payload };
    case "SET_HEALTH":      return { ...state, health: action.payload };
    case "ADD_REASONING":
      return { ...state, reasoningLog: [action.payload, ...state.reasoningLog].slice(0, 80) };
    case "SET_AGENT":
      return { ...state, agentActivity: { ...state.agentActivity, [action.payload.id]: action.payload.status } };
    case "SET_GPU":         return { ...state, gpuUtil: action.payload };
    case "SET_METRICS":     return { ...state, metrics: { ...state.metrics, ...action.payload } };
    case "SET_WS":          return { ...state, wsConnected: action.payload.connected };
    case "INC_WS_EVENT":    return { ...state, wsEventCount: state.wsEventCount + 1 };
    default:                return state;
  }
}

// ── AI Reasoning Seeds ────────────────────────────────────────────────
const AGENTS = ["rca", "cpu", "correlation", "recommendation", "memory", "network", "summarization"];
const AGENT_NAMES: Record<string, string> = {
  rca: "RCA Engine", cpu: "CPU Monitor", correlation: "Correlator",
  recommendation: "Recommender", memory: "Memory Agent",
  network: "Network Monitor", summarization: "Summarizer",
};
const REASONING_SEEDS = [
  { text: "Analyzing memory pressure pattern across payment-service replicas...", kind: "info" as const, agent: "memory" },
  { text: "Cross-referencing pod restart timestamps with network latency spikes...", kind: "info" as const, agent: "correlation" },
  { text: "Confidence threshold met. Correlating OOMKill events with TCP timeout chain...", kind: "success" as const, agent: "rca" },
  { text: "Blast radius estimation: 4 downstream services within propagation depth 3...", kind: "warn" as const, agent: "rca" },
  { text: "Generating autonomous remediation strategy with 94% success probability...", kind: "success" as const, agent: "recommendation" },
  { text: "Validating replica scale-up feasibility against cluster resource quota...", kind: "info" as const, agent: "recommendation" },
  { text: "Emitting recommendation: `kubectl rollout restart deploy/payment-service`", kind: "success" as const, agent: "recommendation" },
  { text: "Health propagation mapped. api-gateway degraded → auth-service timeout...", kind: "warn" as const, agent: "network" },
  { text: "Multi-agent consensus: root cause confirmed. Triggering autonomous patch...", kind: "success" as const, agent: "rca" },
  { text: "GPU inference complete. RTX 3050 Ti at 78% utilisation. Latency 1.2s...", kind: "info" as const, agent: "cpu" },
  { text: "Memory spike detected in catalog-service. RSS 1.8GB exceeds 1.5GB threshold...", kind: "critical" as const, agent: "memory" },
  { text: "Network partition isolated to zone-b. No cross-zone propagation detected...", kind: "warn" as const, agent: "network" },
  { text: "SLA compliance: 99.1%. Within tolerance window. No escalation required.", kind: "success" as const, agent: "summarization" },
  { text: "Summarizing incident INC-0047: cascading failure duration 4.2 minutes...", kind: "info" as const, agent: "summarization" },
];

// ── Context ───────────────────────────────────────────────────────────
interface PlatformContextType {
  state: PlatformState;
  dispatch: React.Dispatch<Action>;
  refreshIncidents: () => Promise<void>;
}

const PlatformContext = createContext<PlatformContextType | null>(null);

const WS_URL = (import.meta as any).env?.VITE_WS_URL || "ws://localhost:8000/ws";

export const PlatformProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);
  const wsRef = useRef<WebSocket | null>(null);
  const seedIdxRef = useRef(0);
  const metricsTickRef = useRef(0);

  // ── Refresh incidents from API ─────────────────────────────────────
  const refreshIncidents = useCallback(async () => {
    try {
      const [incs, topo, health] = await Promise.allSettled([
        api.incidents(),
        api.topology(),
        api.health(),
      ]);
      if (incs.status === "fulfilled") dispatch({ type: "SET_INCIDENTS", payload: incs.value });
      if (topo.status === "fulfilled") dispatch({ type: "SET_TOPOLOGY", payload: topo.value });
      if (health.status === "fulfilled") dispatch({ type: "SET_HEALTH", payload: health.value.status });
    } catch { /* silent */ }
  }, []);

  // ── Persistent WebSocket — lives for the entire app lifetime ───────
  useEffect(() => {
    let pingTimer: ReturnType<typeof setInterval>;
    let reconnectTimer: ReturnType<typeof setTimeout>;

    const connect = () => {
      try {
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;

        ws.onopen = () => {
          dispatch({ type: "SET_WS", payload: { connected: true } });
          pingTimer = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) ws.send("ping");
          }, 30000);
        };

        ws.onclose = () => {
          dispatch({ type: "SET_WS", payload: { connected: false } });
          clearInterval(pingTimer);
          // Auto-reconnect after 3 seconds
          reconnectTimer = setTimeout(connect, 3000);
        };

        ws.onmessage = (msg) => {
          try {
            const event = JSON.parse(msg.data);
            if (event.type === "pong") return;
            dispatch({ type: "INC_WS_EVENT" });

            if (event.type === "topology" && event.payload?.nodes) {
              dispatch({ type: "SET_TOPOLOGY", payload: event.payload });
            }
            if (event.type === "incident" || event.type === "anomaly") {
              refreshIncidents();
            }
            // Push WS reasoning events
            if (event.type === "ai_insight" && event.payload) {
              const agent = String(event.payload.agent ?? "rca");
              const text = String((event.payload.findings as any)?.[0] ?? event.payload.content ?? "");
              if (text) {
                dispatch({
                  type: "ADD_REASONING",
                  payload: {
                    id: Math.random().toString(36).slice(2),
                    agent: AGENT_NAMES[agent] ?? agent,
                    text,
                    ts: new Date().toLocaleTimeString(),
                    kind: "info",
                  },
                });
              }
            }
          } catch { /* ignore malformed */ }
        };
      } catch { /* WebSocket unavailable */ }
    };

    connect();
    return () => {
      clearInterval(pingTimer);
      clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, [refreshIncidents]);

  // ── Initial data fetch ─────────────────────────────────────────────
  useEffect(() => {
    refreshIncidents();
    // Refresh every 20s
    const t = setInterval(refreshIncidents, 20000);
    return () => clearInterval(t);
  }, [refreshIncidents]);

  // ── Synthetic AI reasoning stream (always-on) ──────────────────────
  useEffect(() => {
    const t = setInterval(() => {
      const seed = REASONING_SEEDS[seedIdxRef.current % REASONING_SEEDS.length];
      seedIdxRef.current++;
      dispatch({
        type: "ADD_REASONING",
        payload: {
          id: Math.random().toString(36).slice(2),
          agent: AGENT_NAMES[seed.agent] ?? seed.agent,
          text: seed.text,
          ts: new Date().toLocaleTimeString(),
          kind: seed.kind,
        },
      });
      // Activate the relevant agent
      const agentId = seed.agent;
      dispatch({ type: "SET_AGENT", payload: { id: agentId, status: "thinking" } });
      dispatch({ type: "SET_GPU", payload: 65 + Math.random() * 28 });
      setTimeout(() => {
        dispatch({ type: "SET_AGENT", payload: { id: agentId, status: "active" } });
      }, 2000 + Math.random() * 1500);
    }, 3200);
    return () => clearInterval(t);
  }, []);

  // ── Live metrics oscillator ────────────────────────────────────────
  useEffect(() => {
    const t = setInterval(() => {
      metricsTickRef.current++;
      const tick = metricsTickRef.current;
      dispatch({
        type: "SET_METRICS",
        payload: {
          cpuAvg:     Math.max(15, Math.min(95, 67  + Math.sin(tick * 0.15) * 12 + (Math.random() - 0.5) * 4)),
          memUsage:   Math.max(20, Math.min(92, 74  + Math.sin(tick * 0.08) * 8  + (Math.random() - 0.5) * 2)),
          netMbps:    Math.max(50, Math.min(1900, 892 + Math.sin(tick * 0.2) * 200 + (Math.random() - 0.5) * 80)),
          errorRate:  Math.max(0,  Math.min(120, 23  + Math.sin(tick * 0.12) * 10 + (Math.random() - 0.5) * 5)),
          p99Latency: Math.max(0.2, Math.min(4,  0.7 + Math.sin(tick * 0.18) * 0.5 + (Math.random() - 0.5) * 0.2)),
          slaPercent: Math.max(97.5, Math.min(100, 99.1 + (Math.random() - 0.5) * 0.5)),
        },
      });
    }, 2500);
    return () => clearInterval(t);
  }, []);

  return (
    <PlatformContext.Provider value={{ state, dispatch, refreshIncidents }}>
      {children}
    </PlatformContext.Provider>
  );
};

// ── Hook ──────────────────────────────────────────────────────────────
export function usePlatform() {
  const ctx = useContext(PlatformContext);
  if (!ctx) throw new Error("usePlatform must be used within PlatformProvider");
  return ctx;
}

// Convenience selectors
export const useIncidents = () => usePlatform().state.incidents;
export const useTopology  = () => usePlatform().state.topology;
export const useMetrics   = () => usePlatform().state.metrics;
export const useReasoningLog = () => usePlatform().state.reasoningLog;
export const useAgentActivity = () => usePlatform().state.agentActivity;
export const usePlatformWS = () => {
  const { state } = usePlatform();
  return { connected: state.wsConnected, eventCount: state.wsEventCount };
};
