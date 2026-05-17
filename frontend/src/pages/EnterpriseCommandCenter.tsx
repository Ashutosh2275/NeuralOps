import React, { useEffect, useState } from "react";
import { useWebSocket } from "@/hooks/useWebSocket";

interface PredictedFailure {
  incident_type: string;
  probability: number;
  confidence: number;
  time_to_failure_hours: number;
  severity_forecast: string;
  affected_services: string[];
  reasoning: string;
}

interface RemediationWorkflow {
  workflow_id: string;
  incident_id: string;
  status: string;
  step_count: number;
  confidence: number;
  current_step: number;
}

export const EnterpriseCommandCenter: React.FC = () => {
  const { events, connected } = useWebSocket();
  const [predictions, setPredictions] = useState<PredictedFailure[]>([]);
  const [workflows, setWorkflows] = useState<RemediationWorkflow[]>([]);
  const [metrics, setMetrics] = useState({
    mttr: 0,
    mttd: 0,
    uptime: 99.9,
    slaCompliance: 99.0,
    incidentTrend: 0,
    predictedUptime24h: 99.5,
  });

  // Fetch initial predictions
  useEffect(() => {
    const fetchPredictions = async () => {
      try {
        const res = await fetch(
          "/api/v1/phase13/predictions/forecast/00000000-0000-0000-0000-000000000000"
        );
        const data = await res.json();
        setPredictions(data.predictions || []);
      } catch (error) {
        console.error("Failed to fetch predictions:", error);
      }
    };

    fetchPredictions();
    const interval = setInterval(fetchPredictions, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="enterprise-command-center">
      <Header connected={connected} />

      <div className="main-grid">
        {/* Left: Infrastructure Health Radar */}
        <HealthRadar metrics={metrics} />

        {/* Center: Live Cluster Map with D3 */}
        <LiveClusterMap predictions={predictions} />

        {/* Right: AI Confidence Visualizer */}
        <AIConfidenceVisualizer workflows={workflows} />
      </div>

      {/* Incident Stream */}
      <IncidentStream events={events} />

      {/* Remediation Timeline */}
      <RemediationTimeline workflows={workflows} />

      {/* Executive KPI Board */}
      <ExecutiveKPIBoard metrics={metrics} predictions={predictions} />

      <style>{`
        .enterprise-command-center {
          display: grid;
          grid-template-rows: auto 1fr auto auto auto;
          gap: 16px;
          padding: 20px;
          background: linear-gradient(135deg, #0a0e27 0%, #16213e 100%);
          min-height: 100vh;
          color: #e0e0e0;
          font-family: "JetBrains Mono", monospace;
        }

        .main-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 16px;
          height: 400px;
        }

        .health-radar {
          background: rgba(15, 23, 42, 0.8);
          border: 1px solid rgba(76, 175, 80, 0.3);
          border-radius: 8px;
          padding: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .cluster-map {
          background: rgba(15, 23, 42, 0.8);
          border: 1px solid rgba(76, 175, 80, 0.3);
          border-radius: 8px;
          padding: 16px;
        }

        .confidence-visualizer {
          background: rgba(15, 23, 42, 0.8);
          border: 1px solid rgba(76, 175, 80, 0.3);
          border-radius: 8px;
          padding: 16px;
        }

        .incident-stream {
          background: rgba(15, 23, 42, 0.8);
          border: 1px solid rgba(76, 175, 80, 0.3);
          border-radius: 8px;
          padding: 16px;
          height: 200px;
          overflow-y: auto;
        }

        .remediation-timeline {
          background: rgba(15, 23, 42, 0.8);
          border: 1px solid rgba(76, 175, 80, 0.3);
          border-radius: 8px;
          padding: 16px;
          height: 120px;
        }

        .kpi-board {
          display: grid;
          grid-template-columns: repeat(6, 1fr);
          gap: 16px;
        }

        .kpi-card {
          background: rgba(30, 41, 59, 0.6);
          border: 1px solid rgba(76, 175, 80, 0.2);
          border-radius: 8px;
          padding: 16px;
          text-align: center;
        }

        .kpi-label {
          font-size: 11px;
          color: #94a3b8;
          text-transform: uppercase;
          margin-bottom: 8px;
        }

        .kpi-value {
          font-size: 24px;
          font-weight: bold;
          color: #4CAF50;
        }

        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px;
          background: linear-gradient(135deg, rgba(76, 175, 80, 0.15), rgba(76, 175, 80, 0.05));
          border: 2px solid rgba(76, 175, 80, 0.3);
          border-radius: 8px;
        }

        .header h1 {
          margin: 0;
          color: #4CAF50;
          font-size: 24px;
        }

        .status-indicator {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background: rgba(76, 175, 80, 0.2);
          border-radius: 4px;
        }

        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #4CAF50;
          animation: pulse 2s infinite;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
};

// Sub-components
const Header: React.FC<{ connected: boolean }> = ({ connected }) => (
  <div className="header">
    <h1>🚀 Enterprise Command Center</h1>
    <div className="status-indicator">
      <div className="status-dot"></div>
      <span>{connected ? "Connected" : "Connecting..."}</span>
    </div>
  </div>
);

const HealthRadar: React.FC<{ metrics: any }> = ({ metrics }) => (
  <div className="health-radar">
    <div style={{ textAlign: "center" }}>
      <div style={{ fontSize: "48px", fontWeight: "bold", color: "#4CAF50" }}>
        {metrics.uptime.toFixed(2)}%
      </div>
      <div style={{ fontSize: "12px", color: "#94a3b8" }}>Cluster Uptime</div>
    </div>
  </div>
);

const LiveClusterMap: React.FC<{ predictions: any[] }> = ({ predictions }) => (
  <div className="cluster-map">
    <div style={{ fontSize: "14px", fontWeight: "bold", color: "#4CAF50", marginBottom: "12px" }}>
      📍 Live Topology
    </div>
    <div style={{ fontSize: "11px", color: "#94a3b8" }}>
      {predictions.length} predicted failures in next 24h
    </div>
  </div>
);

const AIConfidenceVisualizer: React.FC<{ workflows: any[] }> = ({ workflows }) => (
  <div className="confidence-visualizer">
    <div style={{ fontSize: "14px", fontWeight: "bold", color: "#4CAF50", marginBottom: "12px" }}>
      🤖 AI Consensus
    </div>
    <div style={{ fontSize: "11px", color: "#94a3b8" }}>
      {workflows.length} active workflows
    </div>
  </div>
);

const IncidentStream: React.FC<{ events: any[] }> = ({ events }) => (
  <div className="incident-stream">
    <div style={{ fontSize: "14px", fontWeight: "bold", color: "#4CAF50", marginBottom: "12px" }}>
      📡 Incident Stream
    </div>
    {events.slice(-10).map((event, i) => (
      <div key={i} style={{ fontSize: "11px", color: "#94a3b8", marginBottom: "4px" }}>
        {event.message || "Event: " + JSON.stringify(event).substring(0, 60) + "..."}
      </div>
    ))}
  </div>
);

const RemediationTimeline: React.FC<{ workflows: any[] }> = ({ workflows }) => (
  <div className="remediation-timeline">
    <div style={{ fontSize: "14px", fontWeight: "bold", color: "#4CAF50", marginBottom: "12px" }}>
      ⚙️ Remediation Progress
    </div>
    {workflows.map((w) => (
      <div key={w.workflow_id} style={{ fontSize: "11px", color: "#94a3b8" }}>
        Workflow: Step {w.current_step}/{w.step_count}
      </div>
    ))}
  </div>
);

const ExecutiveKPIBoard: React.FC<{ metrics: any; predictions: any[] }> = ({ metrics, predictions }) => (
  <div className="kpi-board">
    <KPICard label="MTTR (min)" value={metrics.mttr.toFixed(1)} />
    <KPICard label="MTTD (min)" value={metrics.mttd.toFixed(1)} />
    <KPICard label="Uptime %" value={metrics.uptime.toFixed(2)} />
    <KPICard label="SLA %" value={metrics.slaCompliance.toFixed(1)} />
    <KPICard label="Incident Trend" value={(metrics.incidentTrend > 0 ? "↓" : "↑") + " " + Math.abs(metrics.incidentTrend).toFixed(0)} />
    <KPICard label="Predicted Uptime 24h" value={metrics.predictedUptime24h.toFixed(2)} />
  </div>
);

const KPICard: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="kpi-card">
    <div className="kpi-label">{label}</div>
    <div className="kpi-value">{value}</div>
  </div>
);

export default EnterpriseCommandCenter;
