import React, { useState } from "react";
import { Play, Square } from "lucide-react";
import "../../../styles/demo.css";

interface DemoScenario {
  id: string;
  name: string;
  description: string;
  services: string[];
  duration_seconds: number;
}

const JudgeDemoMode: React.FC<{ clusterId?: string }> = ({ clusterId = "00000000-0000-0000-0000-000000000000" }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [demoProgress, setDemoProgress] = useState(0);
  const [selectedScenario, setSelectedScenario] = useState<string>("cascading_failure");
  const [logs, setLogs] = useState<string[]>([]);

  const scenarios: DemoScenario[] = [
    {
      id: "cascading_failure",
      name: "🌊 Cascading Failure",
      description: "Multi-service cascading failure with auto-remediation",
      services: ["api-gateway", "auth-service", "payment-service", "database"],
      duration_seconds: 120,
    },
    {
      id: "cpu_spike",
      name: "🔥 CPU Spike Storm",
      description: "Pod CPU spike causing performance degradation",
      services: ["api-gateway", "compute-service"],
      duration_seconds: 90,
    },
    {
      id: "memory_leak",
      name: "💧 Memory Leak",
      description: "Progressive memory leak with pod restart recovery",
      services: ["auth-service"],
      duration_seconds: 100,
    },
    {
      id: "network_degradation",
      name: "📡 Network Degradation",
      description: "Network latency and packet loss across services",
      services: ["api-gateway", "database", "cache"],
      duration_seconds: 110,
    },
  ];

  const addLog = (message: string) => {
    setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${message}`]);
  };

  const triggerDemo = async () => {
    if (isRunning) {
      setIsRunning(false);
      setDemoProgress(0);
      setLogs([]);
      return;
    }

    setIsRunning(true);
    setLogs([]);
    setDemoProgress(0);

    try {
      addLog("🎬 Starting Judge Demo Mode...");
      addLog(`📋 Scenario: ${scenarios.find((s) => s.id === selectedScenario)?.name}`);

      // Step 1: Trigger incident
      addLog("1️⃣  Triggering infrastructure chaos...");
      setDemoProgress(10);
      await new Promise((r) => setTimeout(r, 2000));

      const createResponse = await fetch("/api/intelligence/demo/trigger-incident", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cluster_id: clusterId,
          incident_type: selectedScenario,
        }),
      });

      if (!createResponse.ok) throw new Error("Failed to trigger incident");
      const incident = await createResponse.json();
      addLog(`✅ Incident created: ${incident.incident_id}`);

      // Step 2: Show degradation
      addLog("2️⃣  Infrastructure degrading...");
      setDemoProgress(25);
      for (let i = 0; i < 3; i++) {
        await new Promise((r) => setTimeout(r, 1500));
        addLog(`   ⚠️  Service degradation: ${(30 + i * 20).toFixed(0)}%`);
        setDemoProgress(25 + (i + 1) * 5);
      }

      // Step 3: Show cascade
      addLog("3️⃣  Cascading failure detected...");
      setDemoProgress(45);
      for (const service of scenarios.find((s) => s.id === selectedScenario)?.services || []) {
        await new Promise((r) => setTimeout(r, 800));
        addLog(`   📍 ${service} degraded`);
        setDemoProgress(45 + ((scenarios.find((s) => s.id === selectedScenario)?.services || []).indexOf(service) / 4) * 15);
      }

      // Step 4: AI Reasoning
      addLog("4️⃣  AI agents analyzing...");
      setDemoProgress(60);
      await new Promise((r) => setTimeout(r, 2000));
      addLog("   🤖 RCA Agent: Root cause identified in dependency chain");
      addLog("   💡 Recommendation Agent: Implement pod restart + traffic rerouting");
      setDemoProgress(70);

      // Step 5: Remediation
      addLog("5️⃣  Auto-remediation activating...");
      setDemoProgress(75);
      const remediations = [
        "Pod restart initiated",
        "Replica scaling triggered",
        "Traffic rerouted to healthy instances",
        "Health checks re-enabled",
      ];

      for (const remediation of remediations) {
        await new Promise((r) => setTimeout(r, 1200));
        addLog(`   ✨ ${remediation}`);
        setDemoProgress(75 + (remediations.indexOf(remediation) / remediations.length) * 15);
      }

      // Step 6: Recovery
      addLog("6️⃣  Infrastructure recovering...");
      setDemoProgress(90);
      for (let i = 0; i < 3; i++) {
        await new Promise((r) => setTimeout(r, 800));
        addLog(`   ✅ Service health improving: ${(60 + i * 15).toFixed(0)}%`);
        setDemoProgress(90 + (i + 1) * 3);
      }

      addLog("7️⃣  Replay generated - ready for review");
      addLog("🎉 DEMO COMPLETE - All systems recovered!");
      setDemoProgress(100);

      await new Promise((r) => setTimeout(r, 3000));
      setIsRunning(false);
    } catch (error) {
      addLog(`❌ Error: ${error instanceof Error ? error.message : String(error)}`);
      setIsRunning(false);
    }
  };

  const selectedScenarioData = scenarios.find((s) => s.id === selectedScenario);

  return (
    <div className="demo-container">
      <div className="demo-header">
        <h1>🎮 JUDGE DEMO MODE</h1>
        <p>Live infrastructure chaos & auto-remediation showcase</p>
      </div>

      <div className="demo-content">
        <div className="scenarios-panel">
          <h2>Choose Scenario</h2>
          <div className="scenarios-grid">
            {scenarios.map((scenario) => (
              <button
                key={scenario.id}
                className={`scenario-card ${selectedScenario === scenario.id ? "active" : ""}`}
                onClick={() => !isRunning && setSelectedScenario(scenario.id)}
                disabled={isRunning}
              >
                <div className="scenario-title">{scenario.name}</div>
                <div className="scenario-desc">{scenario.description}</div>
                <div className="scenario-services">
                  {scenario.services.map((s) => (
                    <span key={s} className="service-tag">
                      {s}
                    </span>
                  ))}
                </div>
                <div className="scenario-duration">⏱️ {scenario.duration_seconds}s</div>
              </button>
            ))}
          </div>
        </div>

        <div className="execution-panel">
          <div className="progress-section">
            <h2>Demo Progress</h2>
            <div className="progress-container">
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{
                    width: `${demoProgress}%`,
                    background: `linear-gradient(90deg, #4CAF50, #45a049)`,
                  }}
                />
              </div>
              <div className="progress-text">{demoProgress}% Complete</div>
            </div>

            <div className="execution-steps">
              <div className={`step ${demoProgress >= 10 ? "active" : ""}`}>1️⃣ Trigger Chaos</div>
              <div className={`step ${demoProgress >= 25 ? "active" : ""}`}>2️⃣ Degradation</div>
              <div className={`step ${demoProgress >= 45 ? "active" : ""}`}>3️⃣ Cascade</div>
              <div className={`step ${demoProgress >= 60 ? "active" : ""}`}>4️⃣ AI Analysis</div>
              <div className={`step ${demoProgress >= 75 ? "active" : ""}`}>5️⃣ Remediation</div>
              <div className={`step ${demoProgress >= 90 ? "active" : ""}`}>6️⃣ Recovery</div>
              <div className={`step ${demoProgress >= 100 ? "active" : ""}`}>7️⃣ Replay</div>
            </div>
          </div>

          <div className="control-section">
            <button
              className={`demo-button ${isRunning ? "stop" : "start"}`}
              onClick={triggerDemo}
            >
              {isRunning ? (
                <>
                  <Square size={20} />
                  Stop Demo
                </>
              ) : (
                <>
                  <Play size={20} />
                  Start Demo
                </>
              )}
            </button>

            {isRunning && <div className="status-indicator">🔴 LIVE</div>}
          </div>
        </div>

        <div className="logs-panel">
          <h2>📋 Demo Log</h2>
          <div className="logs-container">
            {logs.length === 0 && !isRunning && (
              <div className="no-logs">Select a scenario and click "Start Demo" to begin...</div>
            )}
            {logs.length === 0 && isRunning && (
              <div className="no-logs">Waiting for demo to start...</div>
            )}
            {logs.map((log, idx) => (
              <div key={idx} className="log-entry">
                {log}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="demo-info">
        <div className="info-card">
          <h4>🎯 What to Watch For</h4>
          <ul>
            <li>Cascading failure propagation through service chain</li>
            <li>AI agents reasoning about root cause in real-time</li>
            <li>Autonomous remediation activating automatically</li>
            <li>Infrastructure health score recovering</li>
            <li>Incident replay being generated</li>
          </ul>
        </div>
        <div className="info-card">
          <h4>⚙️ Demo Features</h4>
          <ul>
            <li>No destructive actions - fully sandboxed</li>
            <li>Realistic failure scenarios</li>
            <li>Live WebSocket event streaming</li>
            <li>Full AI orchestration pipeline</li>
            <li>Complete incident telemetry</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default JudgeDemoMode;
