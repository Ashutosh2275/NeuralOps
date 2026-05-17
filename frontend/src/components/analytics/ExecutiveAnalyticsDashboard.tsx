import React, { useEffect, useState } from "react";
import { BarChart3, TrendingDown, Clock, Target } from "lucide-react";

interface ExecutiveMetrics {
  mttr_minutes: number;
  mttd_minutes: number;
  incidents_per_day: number;
  uptime_percent: number;
  sla_compliance_percent: number;
  predicted_uptime_percent: number;
  predicted_incidents: number;
  reliability: number;
  operational_efficiency: number;
}

const ExecutiveAnalyticsDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<ExecutiveMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await fetch(
          "/api/analytics/executive-dashboard/00000000-0000-0000-0000-000000000000"
        );
        if (res.ok) {
          const data = await res.json();
          setMetrics(data.key_metrics || {});
        }
      } catch (error) {
        console.error("Failed to fetch analytics:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const getMetricColor = (value: number, metric: string) => {
    if (metric === "reliability" || metric === "operational_efficiency" || metric === "sla_compliance_percent") {
      return value > 0.9 ? "#4CAF50" : value > 0.75 ? "#ffcc00" : "#ff9900";
    } else if (metric === "mttr_minutes") {
      return value < 5 ? "#4CAF50" : value < 15 ? "#ffcc00" : "#ff9900";
    }
    return "#4CAF50";
  };

  if (loading || !metrics) {
    return <div className="executive-loading">Loading metrics...</div>;
  }

  return (
    <div className="executive-dashboard">
      <div className="executive-header">
        <h1>📊 Executive Analytics Dashboard</h1>
        <p>Infrastructure reliability & operational KPIs</p>
      </div>

      <div className="metrics-grid">
        {/* MTTR Card */}
        <div className="metric-card">
          <div className="metric-icon">⏱️</div>
          <div className="metric-info">
            <div className="metric-label">MTTR</div>
            <div className="metric-title">Mean Time To Recovery</div>
          </div>
          <div className="metric-value" style={{ color: getMetricColor(metrics.mttr_minutes, "mttr_minutes") }}>
            {metrics.mttr_minutes.toFixed(1)} min
          </div>
        </div>

        {/* MTTD Card */}
        <div className="metric-card">
          <div className="metric-icon">🔔</div>
          <div className="metric-info">
            <div className="metric-label">MTTD</div>
            <div className="metric-title">Mean Time To Detection</div>
          </div>
          <div className="metric-value" style={{ color: getMetricColor(metrics.mttd_minutes, "mttr_minutes") }}>
            {metrics.mttd_minutes.toFixed(1)} min
          </div>
        </div>

        {/* Incident Frequency Card */}
        <div className="metric-card">
          <div className="metric-icon">📈</div>
          <div className="metric-info">
            <div className="metric-label">Incident Rate</div>
            <div className="metric-title">Incidents per Day (7-day avg)</div>
          </div>
          <div className="metric-value">{metrics.incidents_per_day.toFixed(2)}</div>
        </div>

        {/* Uptime Card */}
        <div className="metric-card large">
          <div className="metric-icon">📶</div>
          <div className="metric-info">
            <div className="metric-label">Uptime</div>
            <div className="metric-title">Infrastructure Availability</div>
          </div>
          <div className="metric-value" style={{ color: getMetricColor(metrics.uptime_percent, "uptime") }}>
            {metrics.uptime_percent.toFixed(2)}%
          </div>
        </div>

        {/* SLA Compliance Card */}
        <div className="metric-card large">
          <div className="metric-icon">✅</div>
          <div className="metric-info">
            <div className="metric-label">SLA Compliance</div>
            <div className="metric-title">Service Level Agreement</div>
          </div>
          <div className="metric-value" style={{ color: getMetricColor(metrics.sla_compliance_percent, "sla_compliance_percent") }}>
            {metrics.sla_compliance_percent.toFixed(1)}%
          </div>
        </div>

        {/* Reliability Score Card */}
        <div className="metric-card large">
          <div className="metric-icon">💪</div>
          <div className="metric-info">
            <div className="metric-label">Reliability</div>
            <div className="metric-title">Overall Infrastructure Score</div>
          </div>
          <div className="metric-value" style={{ color: getMetricColor(metrics.reliability, "reliability") }}>
            {(metrics.reliability * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Predictions */}
      <div className="predictions-section">
        <h2>🔮 24-Hour Predictions</h2>
        <div className="predictions-grid">
          <div className="prediction-card">
            <div className="prediction-label">Predicted Uptime</div>
            <div className="prediction-value" style={{ color: getMetricColor(metrics.predicted_uptime_percent, "uptime") }}>
              {metrics.predicted_uptime_percent.toFixed(2)}%
            </div>
            <div className="prediction-note">Next 24 hours</div>
          </div>

          <div className="prediction-card">
            <div className="prediction-label">Predicted Incidents</div>
            <div className="prediction-value">{metrics.predicted_incidents}</div>
            <div className="prediction-note">Expected count</div>
          </div>

          <div className="prediction-card">
            <div className="prediction-label">Operational Efficiency</div>
            <div className="prediction-value" style={{ color: getMetricColor(metrics.operational_efficiency, "operational_efficiency") }}>
              {(metrics.operational_efficiency * 100).toFixed(1)}%
            </div>
            <div className="prediction-note">Service optimization</div>
          </div>
        </div>
      </div>

      <style>{`
        .executive-dashboard {
          display: grid;
          grid-template-rows: auto auto 1fr;
          gap: 20px;
          padding: 20px;
          background: linear-gradient(135deg, #0a0e27 0%, #16213e 100%);
          min-height: 100vh;
          color: #e0e0e0;
        }

        .executive-header {
          text-align: center;
          padding: 20px;
          background: linear-gradient(135deg, rgba(76, 175, 80, 0.15), rgba(76, 175, 80, 0.05));
          border: 2px solid rgba(76, 175, 80, 0.3);
          border-radius: 8px;
          box-shadow: 0 0 20px rgba(76, 175, 80, 0.1);
        }

        .executive-header h1 {
          margin: 0 0 4px 0;
          color: #4CAF50;
          font-size: 28px;
          text-shadow: 0 0 10px rgba(76, 175, 80, 0.3);
        }

        .executive-header p {
          margin: 0;
          color: #94a3b8;
          font-size: 12px;
        }

        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 16px;
        }

        .metric-card {
          display: grid;
          grid-template-columns: auto 1fr auto;
          align-items: center;
          gap: 16px;
          background: rgba(15, 23, 42, 0.8);
          border: 1px solid rgba(148, 163, 184, 0.2);
          border-radius: 8px;
          padding: 16px;
          transition: all 0.3s ease;
        }

        .metric-card:hover {
          border-color: rgba(76, 175, 80, 0.4);
          box-shadow: 0 4px 12px rgba(76, 175, 80, 0.1);
        }

        .metric-card.large {
          grid-template-columns: auto 1fr auto;
        }

        .metric-icon {
          font-size: 24px;
          line-height: 1;
        }

        .metric-info {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .metric-label {
          font-size: 11px;
          color: #4CAF50;
          text-transform: uppercase;
          font-weight: bold;
          letter-spacing: 1px;
        }

        .metric-title {
          font-size: 12px;
          color: #94a3b8;
        }

        .metric-value {
          font-size: 24px;
          font-weight: bold;
          text-align: right;
          line-height: 1;
        }

        .predictions-section {
          background: rgba(15, 23, 42, 0.8);
          border: 1px solid rgba(148, 163, 184, 0.2);
          border-radius: 8px;
          padding: 20px;
        }

        .predictions-section h2 {
          margin: 0 0 16px 0;
          color: #4CAF50;
          font-size: 14px;
          text-transform: uppercase;
          letter-spacing: 1px;
        }

        .predictions-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 16px;
        }

        .prediction-card {
          background: linear-gradient(135deg, rgba(76, 175, 80, 0.1), rgba(76, 175, 80, 0.05));
          border: 1px solid rgba(76, 175, 80, 0.2);
          border-radius: 8px;
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .prediction-label {
          font-size: 12px;
          color: #94a3b8;
          text-transform: uppercase;
        }

        .prediction-value {
          font-size: 28px;
          font-weight: bold;
          line-height: 1;
        }

        .prediction-note {
          font-size: 10px;
          color: #4CAF50;
        }

        .executive-loading {
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 100vh;
          color: #4CAF50;
          font-size: 16px;
        }
      `}</style>
    </div>
  );
};

export default ExecutiveAnalyticsDashboard;
