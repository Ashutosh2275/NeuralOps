import React, { useEffect, useState } from "react";
import { TrendingUp, AlertTriangle, Target, Activity } from "lucide-react";

interface Forecast {
  forecast_type: string;
  target_service: string;
  probability: number;
  confidence_score: number;
  severity_prediction: string;
}

interface ServiceHealth {
  service_name: string;
  overall_health: number;
  risk_level: string;
  uptime_score: number;
  stability_score: number;
  metrics: {
    restart_frequency_per_day: number;
    incident_frequency_per_day: number;
    avg_recovery_time_seconds: number;
  };
}

const PredictiveIntelligenceDashboard: React.FC = () => {
  const [forecasts, setForecasts] = useState<Forecast[]>([]);
  const [serviceHealth, setServiceHealth] = useState<ServiceHealth | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch forecasts
        const forecastRes = await fetch(
          "/api/intelligence/forecasts/00000000-0000-0000-0000-000000000000"
        );
        if (forecastRes.ok) {
          const data = await forecastRes.json();
          setForecasts(data.forecasts || []);
        }

        // Fetch service health
        const healthRes = await fetch(
          "/api/intelligence/service-health/00000000-0000-0000-0000-000000000000/api-gateway"
        );
        if (healthRes.ok) {
          const data = await healthRes.json();
          setServiceHealth(data);
        }
      } catch (error) {
        console.error("Failed to fetch intelligence data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
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

  if (loading) {
    return <div className="predictive-loading">Loading intelligence...</div>;
  }

  return (
    <div className="predictive-dashboard">
      <div className="dashboard-header">
        <h1>🔮 Predictive Intelligence Dashboard</h1>
        <p>AI-powered incident forecasting and infrastructure analysis</p>
      </div>

      <div className="dashboard-grid">
        {/* Forecasts Section */}
        <div className="dashboard-section forecasts-section">
          <h2>⚡ Incident Forecasts (24h)</h2>
          <div className="forecasts-list">
            {forecasts.length === 0 ? (
              <p className="no-data">No forecasts at this time</p>
            ) : (
              forecasts.map((forecast, idx) => (
                <div
                  key={idx}
                  className="forecast-card"
                  style={{
                    borderLeftColor: getSeverityColor(forecast.severity_prediction),
                  }}
                >
                  <div className="forecast-header">
                    <span className="forecast-type">{forecast.forecast_type.replace("_", " ").toUpperCase()}</span>
                    <span className="forecast-service">{forecast.target_service}</span>
                  </div>

                  <div className="forecast-metrics">
                    <div className="metric">
                      <span className="metric-label">Probability:</span>
                      <span className="metric-value" style={{ color: getSeverityColor(forecast.severity_prediction) }}>
                        {(forecast.probability * 100).toFixed(1)}%
                      </span>
                    </div>

                    <div className="metric">
                      <span className="metric-label">Confidence:</span>
                      <span className="metric-value" style={{ color: "#4CAF50" }}>
                        {(forecast.confidence_score * 100).toFixed(1)}%
                      </span>
                    </div>

                    <div className="metric">
                      <span className="metric-label">Severity:</span>
                      <span
                        className="metric-value"
                        style={{ color: getSeverityColor(forecast.severity_prediction) }}
                      >
                        {forecast.severity_prediction.toUpperCase()}
                      </span>
                    </div>
                  </div>

                  {forecast.probability > 0.5 && (
                    <div className="forecast-warning">
                      ⚠️ High probability incident - monitor closely
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Service Health Section */}
        {serviceHealth && (
          <div className="dashboard-section health-section">
            <h2>💚 Service Health: {serviceHealth.service_name}</h2>

            <div className="health-scores">
              <div className="score-box">
                <div className="score-title">Overall Health</div>
                <div
                  className="score-large"
                  style={{ color: getHealthColor(serviceHealth.overall_health) }}
                >
                  {(serviceHealth.overall_health * 100).toFixed(1)}%
                </div>
                <div className="score-label">{serviceHealth.risk_level.toUpperCase()} RISK</div>
              </div>

              <div className="health-metrics">
                <div className="health-metric">
                  <span>Uptime</span>
                  <div className="metric-bar">
                    <div
                      className="metric-fill"
                      style={{
                        width: `${serviceHealth.uptime_score * 100}%`,
                        backgroundColor: getHealthColor(serviceHealth.uptime_score),
                      }}
                    />
                  </div>
                  <span className="value">{(serviceHealth.uptime_score * 100).toFixed(1)}%</span>
                </div>

                <div className="health-metric">
                  <span>Stability</span>
                  <div className="metric-bar">
                    <div
                      className="metric-fill"
                      style={{
                        width: `${serviceHealth.stability_score * 100}%`,
                        backgroundColor: getHealthColor(serviceHealth.stability_score),
                      }}
                    />
                  </div>
                  <span className="value">{(serviceHealth.stability_score * 100).toFixed(1)}%</span>
                </div>
              </div>

              <div className="operational-metrics">
                <div className="op-metric">
                  <span className="op-label">Restarts/Day</span>
                  <span className="op-value">{serviceHealth.metrics.restart_frequency_per_day.toFixed(2)}</span>
                </div>

                <div className="op-metric">
                  <span className="op-label">Incidents/Day</span>
                  <span className="op-value">{serviceHealth.metrics.incident_frequency_per_day.toFixed(2)}</span>
                </div>

                <div className="op-metric">
                  <span className="op-label">Avg Recovery</span>
                  <span className="op-value">{Math.round(serviceHealth.metrics.avg_recovery_time_seconds)}s</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Quick Stats */}
        <div className="dashboard-section stats-section">
          <h2>📊 Quick Stats</h2>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon">🎯</div>
              <div className="stat-title">High Risk Forecasts</div>
              <div className="stat-number">
                {forecasts.filter((f) => f.probability > 0.6).length}
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">⚡</div>
              <div className="stat-title">Avg Confidence</div>
              <div className="stat-number">
                {forecasts.length > 0
                  ? (
                      (forecasts.reduce((sum, f) => sum + f.confidence_score, 0) / forecasts.length) *
                      100
                    ).toFixed(0)
                  : "N/A"}
                %
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">🔔</div>
              <div className="stat-title">Total Forecasts</div>
              <div className="stat-number">{forecasts.length}</div>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        .predictive-dashboard {
          display: grid;
          grid-template-rows: auto 1fr;
          gap: 16px;
          padding: 20px;
          background: linear-gradient(135deg, #0a0e27 0%, #16213e 100%);
          min-height: 100vh;
          color: #e0e0e0;
        }

        .dashboard-header {
          text-align: center;
          padding: 16px;
          background: rgba(76, 175, 80, 0.1);
          border: 1px solid rgba(76, 175, 80, 0.3);
          border-radius: 8px;
        }

        .dashboard-header h1 {
          margin: 0 0 4px 0;
          color: #4CAF50;
          font-size: 24px;
        }

        .dashboard-header p {
          margin: 0;
          font-size: 12px;
          color: #94a3b8;
        }

        .dashboard-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
          gap: 16px;
        }

        .dashboard-section {
          background: rgba(15, 23, 42, 0.8);
          border: 1px solid rgba(148, 163, 184, 0.2);
          border-radius: 8px;
          padding: 16px;
          backdrop-filter: blur(10px);
        }

        .dashboard-section h2 {
          margin: 0 0 12px 0;
          color: #4CAF50;
          font-size: 14px;
          text-transform: uppercase;
          letter-spacing: 1px;
        }

        .forecasts-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .forecast-card {
          background: rgba(30, 41, 59, 0.6);
          border-left: 4px solid;
          border-radius: 4px;
          padding: 12px;
          font-size: 12px;
        }

        .forecast-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
          color: #e0e0e0;
        }

        .forecast-type {
          font-weight: bold;
          font-size: 11px;
          text-transform: uppercase;
          color: #4CAF50;
        }

        .forecast-service {
          color: #94a3b8;
        }

        .forecast-metrics {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 8px;
          margin-bottom: 8px;
        }

        .metric {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .metric-label {
          color: #94a3b8;
          font-size: 10px;
        }

        .metric-value {
          font-weight: bold;
          font-size: 11px;
        }

        .forecast-warning {
          background: rgba(255, 68, 68, 0.1);
          border: 1px solid rgba(255, 68, 68, 0.3);
          padding: 6px;
          border-radius: 3px;
          color: #ff9999;
          font-size: 10px;
        }

        .no-data {
          text-align: center;
          color: #94a3b8;
          padding: 16px;
        }

        .health-scores {
          display: grid;
          gap: 12px;
        }

        .score-box {
          background: rgba(76, 175, 80, 0.1);
          border: 1px solid rgba(76, 175, 80, 0.3);
          border-radius: 4px;
          padding: 12px;
          text-align: center;
        }

        .score-title {
          font-size: 11px;
          color: #94a3b8;
          margin-bottom: 4px;
        }

        .score-large {
          font-size: 28px;
          font-weight: bold;
          margin-bottom: 4px;
        }

        .score-label {
          font-size: 10px;
          color: #4CAF50;
          text-transform: uppercase;
        }

        .health-metrics {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .health-metric {
          display: grid;
          grid-template-columns: 80px 1fr 50px;
          align-items: center;
          gap: 8px;
          font-size: 11px;
        }

        .metric-bar {
          height: 6px;
          background: rgba(30, 41, 59, 0.8);
          border-radius: 3px;
          overflow: hidden;
        }

        .metric-fill {
          height: 100%;
          border-radius: 3px;
          box-shadow: 0 0 8px currentColor;
          transition: width 0.3s ease;
        }

        .value {
          text-align: right;
          color: #e0e0e0;
          font-weight: bold;
        }

        .operational-metrics {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 8px;
          margin-top: 12px;
          padding-top: 12px;
          border-top: 1px solid rgba(148, 163, 184, 0.1);
        }

        .op-metric {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .op-label {
          font-size: 9px;
          color: #94a3b8;
          text-transform: uppercase;
        }

        .op-value {
          font-size: 14px;
          font-weight: bold;
          color: #4CAF50;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 12px;
        }

        .stat-card {
          background: rgba(30, 41, 59, 0.6);
          border: 1px solid rgba(76, 175, 80, 0.2);
          border-radius: 4px;
          padding: 12px;
          text-align: center;
        }

        .stat-icon {
          font-size: 20px;
          margin-bottom: 4px;
        }

        .stat-title {
          font-size: 10px;
          color: #94a3b8;
          margin-bottom: 4px;
        }

        .stat-number {
          font-size: 20px;
          font-weight: bold;
          color: #4CAF50;
        }

        .predictive-loading {
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

export default PredictiveIntelligenceDashboard;
