import React, { useEffect, useState } from "react";
import { AlertTriangle, Heart, Zap, Activity } from "lucide-react";
import "../../../styles/warroom.css";

interface HealthMetrics {
  overall_health: number;
  cluster_health: number;
  namespace_health: number;
  service_health: number;
  dependency_health: number;
  incident_risk_score: number;
  recovery_readiness_score: number;
  cascading_failure_probability: number;
}

interface IncidentEvent {
  id: string;
  title: string;
  severity: "critical" | "major" | "moderate" | "minor";
  status: "open" | "in_progress" | "resolved";
  timestamp: string;
  affected_services: number;
}

const WarRoomDashboard: React.FC = () => {
  const [health, setHealth] = useState<HealthMetrics | null>(null);
  const [incidents, setIncidents] = useState<IncidentEvent[]>([]);
  const [activeRemediations, setActiveRemediations] = useState(0);
  const [cascadeActivity, setCascadeActivity] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await fetch("/api/intelligence/health/cluster/00000000-0000-0000-0000-000000000000");
        if (response.ok) {
          const data = await response.json();
          setHealth(data);
        }
      } catch (error) {
        console.error("Failed to fetch health metrics:", error);
      }
    };

    const fetchIncidents = async () => {
      try {
        const response = await fetch("/api/incidents");
        if (response.ok) {
          const data = await response.json();
          setIncidents(data);
        }
      } catch (error) {
        console.error("Failed to fetch incidents:", error);
      }
    };

    fetchHealth();
    fetchIncidents();
    setLoading(false);

    const interval = setInterval(() => {
      fetchHealth();
      fetchIncidents();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "#ff4444";
      case "major":
        return "#ff9900";
      case "moderate":
        return "#ffcc00";
      default:
        return "#4CAF50";
    }
  };

  const getHealthColor = (value: number) => {
    if (value > 0.8) return "#4CAF50";
    if (value > 0.6) return "#ffcc00";
    if (value > 0.4) return "#ff9900";
    return "#ff4444";
  };

  return (
    <div className="warroom-container">
      <div className="warroom-header">
        <h1>🎯 WAR ROOM COMMAND CENTER</h1>
        <div className="warroom-status">
          {health && (
            <div className="status-indicator">
              <Activity size={16} />
              <span style={{ color: getHealthColor(health.overall_health) }}>
                Health: {(health.overall_health * 100).toFixed(1)}%
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="warroom-grid">
        {/* Health Score Section */}
        <div className="warroom-section health-section">
          <h2>⚡ Infrastructure Health</h2>
          {health && (
            <div className="health-metrics">
              <div className="metric">
                <label>Cluster Health</label>
                <div className="metric-bar">
                  <div
                    className="metric-fill"
                    style={{
                      width: `${health.cluster_health * 100}%`,
                      backgroundColor: getHealthColor(health.cluster_health),
                    }}
                  />
                </div>
                <span>{(health.cluster_health * 100).toFixed(1)}%</span>
              </div>

              <div className="metric">
                <label>Service Health</label>
                <div className="metric-bar">
                  <div
                    className="metric-fill"
                    style={{
                      width: `${health.service_health * 100}%`,
                      backgroundColor: getHealthColor(health.service_health),
                    }}
                  />
                </div>
                <span>{(health.service_health * 100).toFixed(1)}%</span>
              </div>

              <div className="metric">
                <label>Dependency Health</label>
                <div className="metric-bar">
                  <div
                    className="metric-fill"
                    style={{
                      width: `${health.dependency_health * 100}%`,
                      backgroundColor: getHealthColor(health.dependency_health),
                    }}
                  />
                </div>
                <span>{(health.dependency_health * 100).toFixed(1)}%</span>
              </div>

              <div className="risk-section">
                <div className="risk-item">
                  <label>Incident Risk</label>
                  <span style={{ color: getHealthColor(1 - health.incident_risk_score) }}>
                    {(health.incident_risk_score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="risk-item">
                  <label>Cascade Probability</label>
                  <span style={{ color: getHealthColor(1 - health.cascading_failure_probability) }}>
                    {(health.cascading_failure_probability * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Active Incidents */}
        <div className="warroom-section incidents-section">
          <h2>🚨 Active Incidents ({incidents.length})</h2>
          <div className="incidents-list">
            {incidents.length === 0 ? (
              <p className="no-incidents">✅ All systems nominal</p>
            ) : (
              incidents.map((incident) => (
                <div
                  key={incident.id}
                  className="incident-item"
                  style={{
                    borderLeftColor: getSeverityColor(incident.severity),
                  }}
                >
                  <div className="incident-header">
                    <span className="incident-severity" style={{ color: getSeverityColor(incident.severity) }}>
                      {incident.severity.toUpperCase()}
                    </span>
                    <span className="incident-title">{incident.title}</span>
                  </div>
                  <div className="incident-meta">
                    <span>Services Affected: {incident.affected_services}</span>
                    <span>Status: {incident.status}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Remediation Activity */}
        <div className="warroom-section remediation-section">
          <h2>🔧 Remediation Activity</h2>
          <div className="remediation-stats">
            <div className="stat-box">
              <div className="stat-number">{activeRemediations}</div>
              <div className="stat-label">Active Remediations</div>
            </div>
            <div className="remediation-actions">
              <div className="action-item">
                <span>Pod Restarts</span>
                <strong>3</strong>
              </div>
              <div className="action-item">
                <span>Replica Scaling</span>
                <strong>2</strong>
              </div>
              <div className="action-item">
                <span>Traffic Rerouting</span>
                <strong>1</strong>
              </div>
            </div>
          </div>
        </div>

        {/* Cascade Visualization */}
        <div className="warroom-section cascade-section">
          <h2>📊 Cascade Propagation</h2>
          <div className="cascade-viz">
            <div className="cascade-layer layer-0">
              <div className="cascade-node">API-GW</div>
            </div>
            <div className="cascade-line" />
            <div className="cascade-layer layer-1">
              <div className="cascade-node dependent">Auth</div>
              <div className="cascade-node dependent">Payment</div>
            </div>
            <div className="cascade-line" />
            <div className="cascade-layer layer-2">
              <div className="cascade-node dependent critical">Database</div>
              <div className="cascade-node dependent">Cache</div>
            </div>
          </div>
        </div>
      </div>

      {/* Timeline at bottom */}
      <div className="warroom-timeline">
        <h3>📍 Incident Timeline</h3>
        <div className="timeline-events">
          {incidents.length > 0 && (
            incidents.map((incident, idx) => (
              <div key={idx} className="timeline-event">
                <div className="timeline-marker" style={{ backgroundColor: getSeverityColor(incident.severity) }} />
                <div className="timeline-content">
                  <strong>{incident.title}</strong>
                  <small>{new Date(incident.timestamp).toLocaleTimeString()}</small>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default WarRoomDashboard;
